# Tienda Canelitos - E-commerce

Sistema de tienda en línea desarrollado con Flask y MySQL.

## Requisitos

- Python 3.8 o superior
- MySQL/MariaDB
- XAMPP (recomendado para desarrollo)

## Configuración inicial

1. Crear un entorno virtual:
```bash
python -m venv venv
```

2. Activar el entorno virtual:
- Windows:
```powershell
.\venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar base de datos:
- Iniciar XAMPP (Apache y MySQL)
- Crear base de datos 'tienda_canelitos'
- Importar el archivo `db_schema.sql`

5. Configurar variables de entorno:
- Copiar `.env.sample` a `.env`
- Ajustar las variables según tu configuración

## Estructura del proyecto

```
tienda_canelitos/
├── app.py             # Aplicación principal
├── requirements.txt   # Dependencias
├── db_schema.sql     # Esquema de base de datos
├── static/           # Archivos estáticos
│   ├── style.css     # Estilos
│   └── img/          # Imágenes
└── templates/        # Plantillas HTML
    ├── admin/       # Vistas de administrador
    ├── seller/      # Vistas de vendedor
    └── delivery/    # Vistas de repartidor
```

## Roles de usuario

- **Admin**: Gestión completa del sistema
- **Seller**: Gestión de productos y pedidos
- **Delivery**: Gestión de entregas
- **Client**: Compras y seguimiento de pedidos

## Características

- Autenticación y roles de usuario
- Catálogo de productos
- Carrito de compras
- Gestión de pedidos
- Panel administrativo
- Reportes de ventas
- Perfiles de usuario
- Seguimiento de entregas

## Desarrollo

1. Activar entorno virtual
2. Iniciar servidor de desarrollo:
```bash
python app.py
```
3. Visitar http://127.0.0.1:5000

## Credenciales de prueba

- Admin:
  - Usuario: admin
  - Contraseña: admin123
- Vendedor:
  - Usuario: vendedor
  - Contraseña: vendedor123
- Repartidor:
  - Usuario: repartidor
  - Contraseña: repartidor123

## Seguridad

- Todas las contraseñas en producción deben ser cambiadas
- Configurar una SECRET_KEY segura en .env
- Mantener actualizado el sistema y dependencias
- Hacer respaldo regular de la base de datos