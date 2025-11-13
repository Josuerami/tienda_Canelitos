-- Reset database tables
DROP TABLE IF EXISTS order_details;
DROP TABLE IF EXISTS orders_master;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS login_history;
DROP TABLE IF EXISTS users;

-- Users table
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'seller', 'delivery', 'client') NOT NULL DEFAULT 'client',
    active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    image VARCHAR(255) DEFAULT 'placeholder.svg',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP
);

-- Login history table
CREATE TABLE login_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    login_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Orders master table
CREATE TABLE orders_master (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    delivery_address TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Pendiente',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Order details table
CREATE TABLE order_details (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders_master(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Insert admin user
INSERT INTO users (username, name, email, password, role)
VALUES ('admin', 'Administrador', 'admin@canelitos.com', 'scrypt:32768:8:1$MO97NxWiTbujIU6A$3faa767c0747f02deb8c6f7cf05f303c61181953134df976bd944bcfe0d437ecfbcfc88a410e416da6f2402d11a5a121f8ce9ad9ea6c3b6b7aee7afa53626d71', 'admin');

-- Insert demo seller
INSERT INTO users (username, name, email, password, role)
VALUES ('vendedor', 'Vendedor Demo', 'vendedor@canelitos.com', 'scrypt:32768:8:1$HKCVaAI1zHxnwcee$0c5bbf3b953d1d6cd0fd0b2c3e7e8b1c6ec34b966e44e41d520c5bbf3b953d1d6cd0fd0b2c3e7e8b1c6ec34b966e44e41d52', 'seller');

-- Insert demo delivery
INSERT INTO users (username, name, email, password, role)
VALUES ('repartidor', 'Repartidor Demo', 'repartidor@canelitos.com', 'scrypt:32768:8:1$zbSBvhqSEuPpDEIx$fcd75356eaa6927b04935e71cff7c724697e3d8b1ad09c6ee38648979d4ea1798e5a6a3da152d8729ae35ceb3d228758c3b8576d198274b4406da8b2add5483e8', 'delivery');

-- Insert some demo products
INSERT INTO products (name, category, description, price, stock) VALUES
('Canela en Polvo 100g', 'Especias', 'Canela molida de alta calidad', 5.99, 50),
('Canela en Rama 50g', 'Especias', 'Ramas de canela selecta', 7.99, 30),
('Mix de Especias', 'Especias', 'Mezcla especial con canela', 9.99, 25),
('Té de Canela', 'Bebidas', 'Té aromático de canela', 4.99, 40),
('Galletas de Canela', 'Repostería', 'Galletas artesanales', 6.99, 35);

COMMIT;