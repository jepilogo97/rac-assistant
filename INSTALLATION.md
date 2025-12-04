# RAC Assistant - Documentación de Instalación y Ejecución

## 📋 Requisitos Previos

### Backend
- Python 3.10 o superior
- pip (gestor de paquetes de Python)

### Frontend
- Node.js 18 o superior
- npm o yarn

## 🚀 Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/jepilogo97/rac-assistant.git
cd rac-assistant
```

### 2. Configurar Backend

```bash
# Instalar dependencias de Python
pip install -r requirements.txt
```

### 3. Configurar Frontend

```bash
# Navegar a la carpeta frontend
cd frontend

# Instalar dependencias de Node
npm install
```

### 4. Configurar Variables de Entorno

#### Frontend

Crear archivo `.env` en la carpeta `frontend`:

```env
VITE_API_URL=http://localhost:8000
```

#### Backend (Opcional)

Si necesitas configurar variables de entorno para el backend, crea un archivo `.env` en la raíz del proyecto.

## ▶️ Ejecución en Desarrollo

### Opción 1: Ejecutar Backend y Frontend por Separado

#### Terminal 1 - Backend (FastAPI)

```bash
# Desde la raíz del proyecto
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El backend estará disponible en: `http://localhost:8000`
- API Docs: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

#### Terminal 2 - Frontend (Vite)

```bash
# Desde la carpeta frontend
cd frontend
npm run dev
```

El frontend estará disponible en: `http://localhost:5173`

### Opción 2: Script de Ejecución Automática (Próximamente)

```bash
# Ejecutar ambos servicios simultáneamente
npm run dev:all
```

## 🔑 Configuración de API Key

1. Obtén tu API Key de Google Gemini en: https://makersuite.google.com/app/apikey
2. En la aplicación web, haz clic en "Configurar API Key" en el header
3. Ingresa tu API Key y guárdala

La API Key se almacenará localmente en tu navegador.

## 📦 Build para Producción

### Backend

```bash
# El backend no requiere build, se ejecuta directamente con uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm run build
```

Los archivos de producción se generarán en `frontend/dist/`

### Servir Frontend en Producción

```bash
cd frontend
npm run preview
```

O usar un servidor web como Nginx o Apache para servir los archivos estáticos.

## 🐳 Docker (Opcional)

### Construir Imágenes

```bash
# Backend
docker build -t rac-assistant-backend -f Dockerfile.backend .

# Frontend
docker build -t rac-assistant-frontend -f Dockerfile.frontend ./frontend
```

### Ejecutar con Docker Compose

```bash
docker-compose up -d
```

Servicios disponibles:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:80`

## 🧪 Testing

### Backend

```bash
# Ejecutar tests (cuando estén disponibles)
pytest
```

### Frontend

```bash
cd frontend
npm run test
```

## 🔧 Troubleshooting

### Error: "Module not found"

```bash
# Backend
pip install -r requirements.txt --force-reinstall

# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Error: "Port already in use"

```bash
# Cambiar puerto del backend
uvicorn main:app --reload --port 8001

# Cambiar puerto del frontend
npm run dev -- --port 3000
```

### Error: "CORS policy"

Verifica que el frontend esté configurado en la lista de orígenes permitidos en `main.py`:

```python
allow_origins=[
    "http://localhost:5173",  # Agregar tu puerto aquí
]
```

## 📚 Recursos Adicionales

- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de Vite](https://vitejs.dev/)
- [Documentación de React](https://react.dev/)
- [Documentación de TailwindCSS](https://tailwindcss.com/)
- [Google Gemini API](https://ai.google.dev/)

## 🆘 Soporte

- GitHub Issues: https://github.com/jepilogo97/rac-assistant/issues
- Email: support@rac-assistant.com
