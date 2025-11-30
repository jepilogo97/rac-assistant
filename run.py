#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAC Assistant - Script de Instalación y Ejecución
Versión: 2.0.0
Compatible con: Windows, Linux, macOS
Python: >= 3.8
"""
        ("README.md", "Documentación"),
        ("QUICKSTART.md", "Guía rápida")
    ]
    
    missing_required = []
    missing_optional = []
    
    print_status("Verificando archivos obligatorios:", "INFO")
    for filename, description in required_files:
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print_status(f"   {filename} ({description}) - {file_size:,} bytes", "OK")
        else:
            print_status(f"   {filename} ({description}) - NO ENCONTRADO", "ERROR")
            missing_required.append(filename)
    
    print_status("\nVerificando archivos opcionales:", "INFO")
    for filename, description in optional_files:
        if os.path.exists(filename):
            print_status(f"   {filename} ({description})", "OK")
        else:
            print_status(f"   {filename} ({description}) - no encontrado", "WARNING")
            missing_optional.append(filename)
    
    if missing_required:
        print_status("\nARCHIVOS CRÍTICOS FALTANTES:", "ERROR")
        for filename in missing_required:
            print_status(f"   - {filename}", "ERROR")
        print_status("Descarga todos los archivos del proyecto antes de continuar", "INFO")
        return False
    
    print_status("\n✓ Todos los archivos obligatorios están presentes", "OK")
    
    if missing_optional:
        print_status("Archivos opcionales faltantes (no críticos):", "WARNING")
        for filename in missing_optional:
            print_status(f"   - {filename}", "WARNING")
    
    return True

def install_dependencies():
    """Instalar dependencias del proyecto"""
    print_section("Instalación de dependencias")
    
    # Verificar si requirements.txt existe
    if not os.path.exists("requirements.txt"):
        print_status("requirements.txt no encontrado", "WARNING")
        print_status("Instalando dependencias manualmente", "INFO")
        return install_manual()
    
    print_status("requirements.txt encontrado", "OK")
    print_status("Instalando dependencias (esto puede tomar varios minutos)", "WAIT")
    print_status("Por favor espera...", "INFO")
    
    # Instalar dependencias
    success, output = run_command(
        "pip install -r requirements.txt --quiet --disable-pip-version-check",
        capture_output=True
    )
    
    if success:
        print_status("✓ Dependencias instaladas correctamente", "OK")
        
        # Verificar instalación de paquetes clave
        print_status("\nVerificando paquetes instalados:", "INFO")
        key_packages = ["streamlit", "pandas", "openpyxl", "google-generativeai", "requests"]
        
        for package in key_packages:
            success_check, version = run_command(
                f"pip show {package} | findstr Version" if platform.system() == "Windows" else f"pip show {package} | grep Version",
                capture_output=True
            )
            if success_check:
                version_num = version.split()[-1] if version else "desconocida"
                print_status(f"   {package}: v{version_num}", "OK")
            else:
                print_status(f"   {package}: no instalado", "WARNING")
        
        return True
    else:
        print_status("Error al instalar desde requirements.txt", "ERROR")
        print_status("Intentando instalación manual de paquetes", "WARNING")
        return install_manual()

def install_manual():
    """Instalar dependencias manualmente una por una"""
        success, _ = run_command(
            f"pip install '{package}{version}' --quiet --disable-pip-version-check",
            capture_output=True
        )
        
        if success:
            print_status(f"   {package} instalado", "OK")
        else:
            print_status(f"   Error instalando {package}", "ERROR")
            failed_packages.append(package)
    
    if failed_packages:
        print_status(f"\nPaquetes con problemas: {', '.join(failed_packages)}", "ERROR")
        print_status("La aplicación puede no funcionar correctamente", "WARNING")
        print_status("Intenta instalar manualmente:", "INFO")
        for package in failed_packages:
            print_status(f"   pip install {package}", "INFO")
        return False
    
    print_status("\n✓ Instalación manual completada", "OK")
    return True

def run_app():
    """Ejecutar la aplicación Streamlit"""
    print_section("Iniciando RAC Assistant")
    
    print_status("Configuración de Streamlit", "INFO")
    print_status("   • La aplicación se abrirá automáticamente en tu navegador", "INFO")
    print_status("   • URL local: http://localhost:8501", "INFO")
    print_status("   • Para acceso en red local: http://<tu-ip>:8501", "INFO")
    
    print_status("\n🎮 Controles:", "INFO")
    print_status("   • Ctrl+C - Detener la aplicación", "INFO")
    print_status("   • F5 en navegador - Recargar", "INFO")
    
    print("\n" + "=" * 70)
    print("🚀 APLICACIÓN EN EJECUCIÓN")
    print("=" * 70)
    print("💡 Abre tu navegador en: http://localhost:8501")
    print("🛑 Para detener: presiona Ctrl+C")
    print("=" * 70 + "\n")
    
    try:
        # Ejecutar Streamlit
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "app.py"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print_status("\nError al ejecutar la aplicación", "ERROR")
        print_status("Posibles causas:", "INFO")
        print_status("   1. Dependencias no instaladas correctamente", "INFO")
        print_status("   2. Puerto 8501 ya en uso", "INFO")
        print_status("   3. Archivos del proyecto corruptos", "INFO")
        print_status("\nIntenta:", "INFO")
        print_status("   streamlit cache clear", "INFO")
        print_status("   python -m streamlit run app.py --server.port 8502", "INFO")
        return False
    except KeyboardInterrupt:
        print("\n")
        print_status("Aplicación detenida por el usuario", "INFO")
        return True
    except Exception as e:
        print_status(f"\nError inesperado: {str(e)}", "ERROR")
        return False
    
    return True

def show_help():
    """Mostrar ayuda y consejos"""
    print_section("Información adicional")
    
    print_status("📚 Documentación:", "INFO")
    print_status("   • README.md - Documentación completa", "INFO")
    
    print_status("\n💡 Consejos:", "INFO")
    print_status("   1. Usa 'IA Local' primero para probar sin API Keys", "INFO")
    print_status("   2. Google Gemini genera los mejores diagramas BPMN", "INFO")
    print_status("   3. Descarga el XML BPMN para usarlo en Camunda/Bizagi", "INFO")
    print_status("   4. Los archivos Excel deben tener 11 columnas específicas", "INFO")
    
    print_status("\n🆘 Soporte:", "INFO")
    print_status("   • GitHub Issues: <tu-repositorio>/issues", "INFO")
    print_status("   • Email: support@rac-assistant.com", "INFO")

def main():
    """Función principal del script"""
    try:
        # Banner de bienvenida
        print_banner()
        
        time.sleep(1)  # Pausa breve para que el usuario lea los mensajes
        run_app()
        
        # Despedida
        print("\n" + "=" * 70)
        print_status("¡Gracias por usar RAC Assistant! 🚀", "OK")
        print("=" * 70 + "\n")
        input("Presiona Enter para salir...")
        
    except KeyboardInterrupt:
        print("\n")
        print_status("Proceso cancelado por el usuario", "INFO")
        sys.exit(0)
    except Exception as e:
        print_status(f"\nError crítico inesperado: {str(e)}", "ERROR")
        print_status("Por favor reporta este error en GitHub", "INFO")
        input("\nPresiona Enter para salir...")
        sys.exit(1)

if __name__ == "__main__":
    main()