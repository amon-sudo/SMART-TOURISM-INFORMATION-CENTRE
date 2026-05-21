DO $$
DECLARE
    v_user_id UUID := gen_random_uuid();
    v_admin_role_id TEXT;
BEGIN
    SELECT id INTO v_admin_role_id FROM roles WHERE name = 'admin';

    IF v_admin_role_id IS NULL THEN
        RAISE EXCEPTION 'Admin role not found. Run seed_roles.py first.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM users WHERE email = 'admin@admin.com') THEN
        INSERT INTO users (id, email, username, password_hash, is_active, created_at, updated_at)
        VALUES (
            v_user_id,
            'admin@admin.com',
            'admin',
            'scrypt:32768:8:1$3tKjW8FSyGZXVOZG$3bd568bb0463966d2cd7a4b4cad7e5ad7a78e0056b57ac307c4fcc87190588c3d88f66fc5799375c66c1e57e2aadd8a834800068b4b0dad06aad469f97816f52',
            true,
            now(),
            now()
        );

        INSERT INTO user_roles (user_id, role_id, assigned_at)
        VALUES (v_user_id, v_admin_role_id, now());

        INSERT INTO user_profiles (user_id, full_name, language_preference, currency_preference, timezone, created_at, updated_at)
        VALUES (v_user_id, 'Admin', 'en', 'KES', 'Africa/Nairobi', now(), now());

        INSERT INTO user_notifications (user_id, updated_at)
        VALUES (v_user_id, now());

        RAISE NOTICE 'Admin user created: admin@admin.com';
    ELSE
        RAISE NOTICE 'Admin user already exists, skipping.';
    END IF;
END $$;
