import winreg
import tkinter as tk
from tkinter import messagebox, ttk

# Función para buscar claves en el registro
def search_registry(hive, search_word, path="", results=None):
    if results is None:
        results = []

    try:
        key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ) if path else hive
        i = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(key, i)
                full_path = f"{path}\\{subkey_name}" if path else subkey_name
                if search_word.lower() in subkey_name.lower():
                    results.append(("Clave", hive, full_path, None, None, False))
                search_registry(hive, search_word, full_path, results)
                i += 1
            except OSError:
                break

        i = 0
        while True:
            try:
                value_name, value_data, _ = winreg.EnumValue(key, i)
                if search_word.lower() in value_name.lower() or search_word.lower() in str(value_data).lower():
                    results.append(("Valor", hive, path, value_name, value_data, False))
                i += 1
            except OSError:
                break

        if path:
            winreg.CloseKey(key)

    except (PermissionError, OSError, ValueError):
        pass

    return results

# Función mejorada para eliminar claves con subclaves
def delete_registry_key(hive, key_path):
    try:
        key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_ALL_ACCESS)
        
        # Eliminar subclaves antes de eliminar la clave principal
        while True:
            try:
                subkey = winreg.EnumKey(key, 0)
                delete_registry_key(hive, f"{key_path}\\{subkey}")  
            except OSError:
                break

        winreg.CloseKey(key)  # Cerrar la clave antes de eliminarla
        winreg.DeleteKey(hive, key_path)  # Eliminar la clave principal
        print(f"Clave eliminada: {key_path}")

    except PermissionError:
        print(f"⚠️ No tienes permisos para eliminar {key_path}. Ejecuta como administrador.")
    except FileNotFoundError:
        print(f"ℹ️ La clave {key_path} no existe.")
    except Exception as e:
        print(f"❌ Error al eliminar {key_path}: {e}")

# Función para eliminar registros seleccionados
def delete_selected(results, check_vars, result_window):
    for i, result in enumerate(results):
        if i < len(check_vars) and check_vars[i].get():  # Verificar que el índice esté dentro del rango
            tipo, hive, ruta, nombre, _, _ = result
            try:
                if tipo == "Clave":
                    delete_registry_key(hive, ruta)
                elif tipo == "Valor":
                    key = winreg.OpenKey(hive, ruta, 0, winreg.KEY_SET_VALUE)
                    winreg.DeleteValue(key, nombre)
                    winreg.CloseKey(key)
                    print(f"✅ Valor eliminado: {nombre} en {ruta}")
            except Exception as e:
                print(f"❌ Error al eliminar {ruta}: {e}")

    messagebox.showinfo("Eliminación", "Registros eliminados correctamente.")
    # No cerrar la ventana de resultados después de eliminar
    # result_window.destroy()  # Elimina esta línea si quieres que la ventana permanezca abierta

# Función para mostrar los resultados con paginación
def show_results(results):
    result_window = tk.Toplevel()
    result_window.title("Resultados de la búsqueda")
    result_window.geometry("800x600")

    main_frame = tk.Frame(result_window)
    main_frame.pack(fill="both", expand=True)

    button_frame = tk.Frame(main_frame)
    button_frame.pack(fill="x", pady=5)

    def select_all():
        for var in check_vars:
            var.set(True)

    btn_select_all = tk.Button(button_frame, text="Seleccionar Todo", command=select_all)
    btn_select_all.pack(side="left", padx=5)

    btn_delete_selected = tk.Button(button_frame, text="Eliminar Seleccionados", command=lambda: delete_selected(results, check_vars, result_window))
    btn_delete_selected.pack(side="left", padx=5)

    # Botón para cerrar la ventana de resultados
    btn_close = tk.Button(button_frame, text="Cerrar", command=result_window.destroy)
    btn_close.pack(side="right", padx=5)

    # Contenedor para el Canvas y las barras de desplazamiento
    container = tk.Frame(main_frame)
    container.pack(fill="both", expand=True)

    # Canvas para contener los resultados
    canvas = tk.Canvas(container)
    canvas.pack(side="left", fill="both", expand=True)

    # Barra de desplazamiento vertical
    v_scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    v_scrollbar.pack(side="right", fill="y")

    # Barra de desplazamiento horizontal
    h_scrollbar = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)
    h_scrollbar.pack(side="bottom", fill="x")

    # Configurar el Canvas para usar las barras de desplazamiento
    canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

    # Frame interno para los resultados
    inner_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=inner_frame, anchor="nw")

    # Actualizar la región de desplazamiento cuando cambie el tamaño del inner_frame
    def update_scrollregion(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    inner_frame.bind("<Configure>", update_scrollregion)

    # Función para mover la barra de desplazamiento horizontal a una posición específica
    def move_horizontal_scroll(position):
        canvas.xview_moveto(position)  # Mueve la barra de desplazamiento horizontal a la posición especificada

    # Variables para la paginación
    page_size = 50  # Número de resultados por página
    current_page = 0
    total_pages = (len(results) + page_size - 1) // page_size

    # Lista para almacenar las variables de los checkboxes
    check_vars = [tk.BooleanVar() for _ in range(len(results))]  # Crear una lista de BooleanVar para todos los resultados

    # Función para mostrar una página específica
    def show_page(page):
        nonlocal current_page
        current_page = page
        for widget in inner_frame.winfo_children():
            widget.destroy()

        start = page * page_size
        end = start + page_size
        page_results = results[start:end]

        for i, result in enumerate(page_results):
            tipo, _, ruta, nombre, datos, _ = result
            check_var = check_vars[start + i]  # Usar el índice correcto en check_vars

            row_frame = tk.Frame(inner_frame)
            row_frame.pack(fill="x", pady=2)

            tk.Checkbutton(row_frame, variable=check_var).pack(side="left", padx=5)
            tk.Label(row_frame, text=f"Tipo: {tipo}").pack(side="left", padx=5)
            tk.Label(row_frame, text=f"Ruta: {ruta}").pack(side="left", padx=5)
            if nombre:
                tk.Label(row_frame, text=f"Nombre: {nombre}").pack(side="left", padx=5)
            if datos:
                tk.Label(row_frame, text=f"Datos: {datos}").pack(side="left", padx=5)

        # Actualizar la etiqueta de la página
        page_label.config(text=f"Página {current_page + 1} de {total_pages}")

        # Mover la barra de desplazamiento horizontal a la posición deseada (por ejemplo, 50%)
        move_horizontal_scroll(0.5)  # Ajusta este valor según la posición que desees

    # Controles de paginación
    pagination_frame = tk.Frame(main_frame)
    pagination_frame.pack(fill="x", pady=5)

    btn_prev = tk.Button(pagination_frame, text="Anterior", command=lambda: show_page(current_page - 1) if current_page > 0 else None)
    btn_prev.pack(side="left", padx=5)

    btn_next = tk.Button(pagination_frame, text="Siguiente", command=lambda: show_page(current_page + 1) if current_page < total_pages - 1 else None)
    btn_next.pack(side="left", padx=5)

    page_label = tk.Label(pagination_frame, text=f"Página {current_page + 1} de {total_pages}")
    page_label.pack(side="left", padx=5)

    # Mostrar la primera página
    show_page(current_page)

# Función para iniciar la búsqueda
def start_search():
    search_word = entry_search.get()
    if not search_word:
        messagebox.showerror("Error", "Ingresa una palabra para buscar.")
        return

    selected_hives = []
    if var_hklm.get():
        selected_hives.append(("HKEY_LOCAL_MACHINE", winreg.HKEY_LOCAL_MACHINE))
    if var_hkcu.get():
        selected_hives.append(("HKEY_CURRENT_USER", winreg.HKEY_CURRENT_USER))
    if var_hkcr.get():
        selected_hives.append(("HKEY_CLASSES_ROOT", winreg.HKEY_CLASSES_ROOT))
    if var_hku.get():
        selected_hives.append(("HKEY_USERS", winreg.HKEY_USERS))
    if var_hkcc.get():
        selected_hives.append(("HKEY_CURRENT_CONFIG", winreg.HKEY_CURRENT_CONFIG))

    if not selected_hives:
        messagebox.showerror("Error", "Selecciona al menos una clave del registro.")
        return

    results = []
    for hive_name, hive in selected_hives:
        try:
            search_registry(hive, search_word, "", results)
        except Exception as e:
            print(f"⚠️ Error en {hive_name}: {e}")

    if not results:
        messagebox.showinfo("Resultados", "No se encontraron coincidencias.")
    else:
        show_results(results)

# Crear la ventana principal
root = tk.Tk()
root.title("Buscador en el Registro")
root.geometry("400x350")

tk.Label(root, text="Palabra a buscar:").pack(pady=5)
entry_search = tk.Entry(root, width=40)
entry_search.pack(pady=5)

var_hklm, var_hkcu, var_hkcr, var_hku, var_hkcc = tk.BooleanVar(), tk.BooleanVar(), tk.BooleanVar(), tk.BooleanVar(), tk.BooleanVar()
tk.Checkbutton(root, text="HKEY_LOCAL_MACHINE", variable=var_hklm).pack(anchor="w")
tk.Checkbutton(root, text="HKEY_CURRENT_USER", variable=var_hkcu).pack(anchor="w")
tk.Checkbutton(root, text="HKEY_CLASSES_ROOT", variable=var_hkcr).pack(anchor="w")
tk.Checkbutton(root, text="HKEY_USERS", variable=var_hku).pack(anchor="w")
tk.Checkbutton(root, text="HKEY_CURRENT_CONFIG", variable=var_hkcc).pack(anchor="w")

tk.Button(root, text="Buscar", command=start_search).pack(pady=10)

root.mainloop()
