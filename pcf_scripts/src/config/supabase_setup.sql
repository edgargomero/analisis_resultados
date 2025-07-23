-- CEAPSI - Script de configuración inicial para Supabase
-- Ejecutar en: Supabase Dashboard > SQL Editor > New query

-- 1. Crear tabla de usuarios
CREATE TABLE IF NOT EXISTS ceapsi_users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(20) DEFAULT 'viewer' CHECK (role IN ('admin', 'analista', 'viewer')),
    password_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP
);

-- 2. Crear índices para mejor rendimiento
CREATE INDEX IF NOT EXISTS idx_ceapsi_users_username ON ceapsi_users(username);
CREATE INDEX IF NOT EXISTS idx_ceapsi_users_email ON ceapsi_users(email);
CREATE INDEX IF NOT EXISTS idx_ceapsi_users_role ON ceapsi_users(role);
CREATE INDEX IF NOT EXISTS idx_ceapsi_users_active ON ceapsi_users(is_active);

-- 3. Habilitar Row Level Security (RLS)
ALTER TABLE ceapsi_users ENABLE ROW LEVEL SECURITY;

-- 4. Crear política para que los usuarios puedan leer su propia información
CREATE POLICY "Users can view their own data" ON ceapsi_users
    FOR SELECT USING (auth.uid() = id::text OR role = 'admin');

-- 5. Crear política para que solo admins puedan insertar/actualizar usuarios
CREATE POLICY "Only admins can insert users" ON ceapsi_users
    FOR INSERT WITH CHECK (role = 'admin');

CREATE POLICY "Only admins can update users" ON ceapsi_users
    FOR UPDATE USING (role = 'admin');

-- 6. Crear política para que admins puedan eliminar usuarios
CREATE POLICY "Only admins can delete users" ON ceapsi_users
    FOR DELETE USING (role = 'admin');

-- 7. Verificar que la tabla se creó correctamente
SELECT 
    'Tabla ceapsi_users creada exitosamente' as status,
    COUNT(*) as total_users
FROM ceapsi_users;

-- Nota: Los usuarios se crearán desde la aplicación Python
-- usando el sistema de autenticación integrado