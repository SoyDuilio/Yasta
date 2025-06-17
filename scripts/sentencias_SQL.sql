-- Sentencias SQL para resetear el estado de prueba del usuario con id=22

-- Paso 1: Revertir el estado del usuario en la tabla 'users'
UPDATE users
SET 
    role = 'authenticated',
    sol_validation_status = 'not_submitted'
WHERE 
    id = 22;

-- Paso 2: Eliminar la relación entre el usuario y el perfil de cliente.
-- Esto es crucial para poder volver a crearla en la siguiente prueba.
DELETE FROM user_client_accesses 
WHERE 
    user_id = 22 AND client_profile_id = 1;

-- Paso 3: Eliminar las credenciales SOL que se guardaron incorrectamente.
DELETE FROM sunat_credentials 
WHERE 
    owner_client_profile_id = 1;

-- (Opcional) Paso 4: Corregir el nombre en client_profiles para que tus futuras
-- pruebas partan de un dato correcto.
UPDATE client_profiles
SET
    business_name = 'DUILIO CESAR RESTUCCIA ESLAVA'
WHERE
    id = 1;