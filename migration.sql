================================================================================
🔧 Loading configuration: DevelopmentConfig
   Environment: DEVELOPMENT
================================================================================
================================================================================
🚀 Starting Lenny Media API
   Environment: DEVELOPMENT
   Debug Mode: True
   Version: 1.0.0
================================================================================
🗄️  Database: PostgreSQL (ep-winter-credit-agrghduc.c-2.eu-central-1.pg.koyeb.app/koyebdb)
🌍 Frontend: https://lennymedia.netlify.app
🌐 CORS Origins: 7 configured
🔐 JWT Cookie Secure: False
🍪 JWT Cookie SameSite: Lax
================================================================================
2026-01-05 12:17:14,834 INFO sqlalchemy.engine.Engine select pg_catalog.version()
2026-01-05 12:17:14,834 INFO sqlalchemy.engine.Engine [raw sql] {}
2026-01-05 12:17:15,180 INFO sqlalchemy.engine.Engine select current_schema()
2026-01-05 12:17:15,181 INFO sqlalchemy.engine.Engine [raw sql] {}
2026-01-05 12:17:15,510 INFO sqlalchemy.engine.Engine show standard_conforming_strings
2026-01-05 12:17:15,511 INFO sqlalchemy.engine.Engine [raw sql] {}
2026-01-05 12:17:15,850 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2026-01-05 12:17:15,852 INFO sqlalchemy.engine.Engine SELECT 1
2026-01-05 12:17:15,852 INFO sqlalchemy.engine.Engine [generated in 0.00050s] {}
✅ Database connection verified
2026-01-05 12:17:16,192 INFO sqlalchemy.engine.Engine ROLLBACK
✅ Flask extensions initialized
✅ Cloudinary configured: dcmy5gkqr
✅ CORS configured for 7 origins
✅ Email service initialized: dannykhan614@gmail.com
✅ Cloudinary service initialized
✅ Routes registered: auth, services, bookings, quotes, dashboard
================================================================================
✅ Lenny Media API initialization complete
   Routes: auth, services, bookings, quotes, dashboard
================================================================================
BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 18a4e23bc91a

CREATE TABLE business_info (
    id SERIAL NOT NULL, 
    business_name VARCHAR(255) NOT NULL, 
    address TEXT NOT NULL, 
    phone_primary VARCHAR(20) NOT NULL, 
    phone_secondary VARCHAR(20), 
    email_primary VARCHAR(255) NOT NULL, 
    email_support VARCHAR(255), 
    hours_of_operation JSON NOT NULL, 
    social_media JSON, 
    google_maps_embed_url TEXT, 
    latitude DECIMAL(10, 8), 
    longitude DECIMAL(11, 8), 
    is_active BOOLEAN NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TYPE contactmessagestatus AS ENUM ('UNREAD', 'READ', 'REPLIED');

CREATE TABLE contact_messages (
    id SERIAL NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    phone VARCHAR(20), 
    subject VARCHAR(255), 
    message TEXT NOT NULL, 
    status contactmessagestatus NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TYPE servicecategory AS ENUM ('PHOTOGRAPHY', 'VIDEOGRAPHY');

CREATE TABLE services (
    id SERIAL NOT NULL, 
    category servicecategory NOT NULL, 
    title VARCHAR(255) NOT NULL, 
    slug VARCHAR(255) NOT NULL, 
    description TEXT, 
    price_min DECIMAL(10, 2), 
    price_max DECIMAL(10, 2), 
    price_display VARCHAR(100), 
    features JSON, 
    is_active BOOLEAN NOT NULL, 
    is_featured BOOLEAN NOT NULL, 
    display_order INTEGER NOT NULL, 
    icon_name VARCHAR(50), 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (slug)
);

CREATE TYPE userrole AS ENUM ('ADMIN', 'PHOTOGRAPHER', 'VIDEOGRAPHY', 'STAFF');

CREATE TABLE users (
    id SERIAL NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    password VARCHAR(255), 
    full_name VARCHAR(255) NOT NULL, 
    role userrole NOT NULL, 
    phone VARCHAR(20), 
    avatar_url TEXT, 
    avatar_public_id VARCHAR(255), 
    is_active BOOLEAN NOT NULL, 
    last_login TIMESTAMP WITHOUT TIME ZONE, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (email)
);

CREATE TYPE bookingstatus AS ENUM ('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED');

CREATE TABLE bookings (
    id SERIAL NOT NULL, 
    client_name VARCHAR(255) NOT NULL, 
    client_phone VARCHAR(20) NOT NULL, 
    client_email VARCHAR(255) NOT NULL, 
    service_type VARCHAR(255) NOT NULL, 
    preferred_date DATE NOT NULL, 
    preferred_time TIME WITHOUT TIME ZONE, 
    location TEXT, 
    budget_range VARCHAR(50), 
    additional_notes TEXT, 
    status bookingstatus NOT NULL, 
    assigned_to INTEGER, 
    internal_notes TEXT, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    confirmed_at TIMESTAMP WITHOUT TIME ZONE, 
    completed_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(assigned_to) REFERENCES users (id)
);

CREATE TYPE cohortstatus AS ENUM ('UPCOMING', 'ACTIVE', 'COMPLETED', 'CANCELLED');

CREATE TABLE cohorts (
    id SERIAL NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    start_date DATE NOT NULL, 
    end_date DATE NOT NULL, 
    max_students INTEGER NOT NULL, 
    current_enrollment INTEGER NOT NULL, 
    status cohortstatus NOT NULL, 
    course_fee DECIMAL(10, 2) NOT NULL, 
    registration_fee DECIMAL(10, 2) NOT NULL, 
    schedule_details TEXT, 
    instructor_id INTEGER, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(instructor_id) REFERENCES users (id)
);

CREATE TYPE portfoliocategory AS ENUM ('WEDDINGS', 'PORTRAITS', 'EVENTS', 'COMMERCIAL');

CREATE TABLE portfolio_items (
    id SERIAL NOT NULL, 
    title VARCHAR(255) NOT NULL, 
    category portfoliocategory NOT NULL, 
    image_url TEXT NOT NULL, 
    thumbnail_url TEXT, 
    description TEXT, 
    client_name VARCHAR(255), 
    shoot_date DATE, 
    location VARCHAR(255), 
    is_featured BOOLEAN NOT NULL, 
    is_published BOOLEAN NOT NULL, 
    display_order INTEGER NOT NULL, 
    alt_text TEXT, 
    tags JSON, 
    instructor_id INTEGER, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(instructor_id) REFERENCES users (id)
);

CREATE TYPE quotestatus AS ENUM ('PENDING', 'SENT', 'ACCEPTED', 'REJECTED', 'CANCELLED');

CREATE TABLE quote_requests (
    id SERIAL NOT NULL, 
    client_name VARCHAR(255) NOT NULL, 
    client_email VARCHAR(255) NOT NULL, 
    client_phone VARCHAR(20) NOT NULL, 
    company_name VARCHAR(255), 
    selected_services JSON NOT NULL, 
    event_date DATE, 
    event_time TIME WITHOUT TIME ZONE, 
    event_location TEXT, 
    budget_range VARCHAR(50), 
    project_description TEXT, 
    referral_source VARCHAR(50), 
    has_conflict BOOLEAN NOT NULL, 
    conflict_checked_at TIMESTAMP WITHOUT TIME ZONE, 
    status quotestatus NOT NULL, 
    quoted_amount DECIMAL(10, 2), 
    quote_details TEXT, 
    quote_sent_at TIMESTAMP WITHOUT TIME ZONE, 
    valid_until DATE, 
    cancelled_at TIMESTAMP WITHOUT TIME ZONE, 
    assigned_to INTEGER, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(assigned_to) REFERENCES users (id)
);

CREATE INDEX idx_quote_datetime ON quote_requests (event_date, event_time, status);

CREATE INDEX ix_quote_requests_client_email ON quote_requests (client_email);

CREATE INDEX ix_quote_requests_created_at ON quote_requests (created_at);

CREATE INDEX ix_quote_requests_event_date ON quote_requests (event_date);

CREATE INDEX ix_quote_requests_event_time ON quote_requests (event_time);

CREATE INDEX ix_quote_requests_status ON quote_requests (status);

CREATE TYPE emaillogstatus AS ENUM ('SENT', 'FAILED', 'PENDING');

CREATE TABLE email_logs (
    id SERIAL NOT NULL, 
    recipient_email VARCHAR(255) NOT NULL, 
    subject VARCHAR(255), 
    template_name VARCHAR(100), 
    status emaillogstatus NOT NULL, 
    user_id INTEGER, 
    related_booking_id INTEGER, 
    related_quote_id INTEGER, 
    sent_at TIMESTAMP WITHOUT TIME ZONE, 
    error_message TEXT, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(related_booking_id) REFERENCES bookings (id), 
    FOREIGN KEY(related_quote_id) REFERENCES quote_requests (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TYPE enrollmentstatus AS ENUM ('PENDING', 'INTERVIEW_SCHEDULED', 'ACCEPTED', 'REJECTED', 'ENROLLED', 'COMPLETED');

CREATE TABLE enrollments (
    id SERIAL NOT NULL, 
    full_name VARCHAR(255) NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    phone VARCHAR(20) NOT NULL, 
    age INTEGER, 
    education_occupation TEXT, 
    experience_level VARCHAR(50), 
    has_own_camera BOOLEAN NOT NULL, 
    learning_goals TEXT, 
    preferred_intake VARCHAR(50), 
    cohort_id INTEGER, 
    status enrollmentstatus NOT NULL, 
    registration_fee_paid BOOLEAN NOT NULL, 
    payment_reference VARCHAR(100), 
    reviewed_by INTEGER, 
    admin_notes TEXT, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(cohort_id) REFERENCES cohorts (id), 
    FOREIGN KEY(reviewed_by) REFERENCES users (id)
);

INSERT INTO alembic_version (version_num) VALUES ('18a4e23bc91a') RETURNING alembic_version.version_num;

COMMIT;

