-- ============================================================================
-- AGENTIC RAG DATABASE MIGRATION - AUTH UPDATE
-- File: 002_add_authentication.sql
-- Purpose: Add authentication tables and update schema for user management
-- ============================================================================

-- ============================================================================
-- TABLE 1: genders (Gender options with descriptions)
-- ============================================================================
CREATE TABLE IF NOT EXISTS genders (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NOT NULL
);

-- ============================================================================
-- TABLE 2: users (Authentication and basic user info)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- NULL for Google OAuth users
    google_id VARCHAR(255) UNIQUE,  -- NULL for password users

    -- Personal information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    gender_id INT REFERENCES genders(id),

    -- Account status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE 3: sessions (JWT sessions for authentication)
-- ============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- UPDATE TABLE 4: user_profiles (Extended user data & long-term learning)
-- ============================================================================
-- Rename user_id to user_profile_id in related tables and update references
-- Note: This migration assumes existing data; in production, you'd need data migration

-- Add user_id_fk to user_profiles
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS user_id INT REFERENCES users(id) ON DELETE CASCADE;

-- Remove old fields from user_profiles that are now in users
ALTER TABLE user_profiles DROP COLUMN IF EXISTS first_name;
ALTER TABLE user_profiles DROP COLUMN IF EXISTS last_name;
ALTER TABLE user_profiles DROP COLUMN IF EXISTS email;

-- Update foreign key references in other tables
-- ShortTermMemory
ALTER TABLE short_term_memory RENAME COLUMN user_id TO user_profile_id;
-- SessionLog
ALTER TABLE session_log RENAME COLUMN user_id TO user_profile_id;
-- CrisisEvent
ALTER TABLE crisis_event RENAME COLUMN user_id TO user_profile_id;
-- UserFeedback
ALTER TABLE user_feedback RENAME COLUMN user_id TO user_profile_id;
-- ConversationMetrics
ALTER TABLE conversation_metrics RENAME COLUMN user_id TO user_profile_id;

-- ============================================================================
-- INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

-- ============================================================================
-- INSERT GENDER DATA
-- ============================================================================
INSERT INTO genders (name, description) VALUES
('Male', 'Traditional male gender identity'),
('Female', 'Traditional female gender identity'),
('Other', 'Select from additional options'),
('Agender', 'A person who does not identify themselves with or experience any gender. Agender people are also called null-gender, genderless, gendervoid, or neutral gender.'),
('Abimegender', 'Associated with being profound, deep, and infinite. The term abimegender may be used alone or in combination with other genders.'),
('Adamas gender', 'A gender that is indefinable or indomitable. People identifying with this gender refuse to be categorized in any particular gender identity.'),
('Aerogender', 'Also called evaisgender, this gender identity changes according to one''s surroundings.'),
('Aesthetigender', 'Also called aesthetgender, it is a type of gender identity derived from aesthetics.'),
('Affectugender', 'This is based on the person''s mood swings or fluctuations.'),
('Agenderflux', 'A person with this gender identity is mostly agender with brief shifts of belonging to other gender types.'),
('Alexigender', 'The person has a fluid gender identity between more than one type of gender although they cannot name the genders they feel fluid in.'),
('Aliusgender', 'This gender identity stands apart from existing social gender constructs. It means having a strong specific gender identity that is neither male nor female.'),
('Amaregender', 'Having a gender identity that changes depending on the person one is emotionally attached to.'),
('Ambigender', 'Having two specific gender identities simultaneously without any fluidity or fluctuations.'),
('Ambonec', 'The person identifies themselves as both man and woman and yet does not belong to either.'),
('Amicagender', 'A gender-fluid identity where a person changes their gender depending on the friends they have.'),
('Androgyne', 'A person feels a combination of feminine and masculine genders.'),
('Anesigender', 'The person feels close to a specific type of gender despite being more comfortable in closely identifying themselves with another gender.'),
('Angenital', 'The person desires to be without any primary sexual characteristics although they do not identify themselves as genderless.'),
('Anogender', 'The gender identity fades in and out in intensity but always comes back to the same gendered feeling.'),
('Anongender', 'The person has a gender identity but does not label it or would prefer to not have a label.'),
('Antegender', 'A protean gender that can be anything but is formless and motionless.'),
('Anxiegender', 'This gender identity has anxiety as its prominent characteristic.'),
('Apagender', 'The person has apathy or a lack of feelings toward one''s gender identity.'),
('Apconsugender', 'It means knowing what are not the characteristics of gender but not knowing what are its characteristics. Thus, a person hides its primary characteristics from the individual.'),
('Astergender', 'The person has a bright and celestial gender identity.'),
('Astral gender', 'Having a gender identity that feels to be related to space.'),
('Autigender', 'Having a gender identity that feels to be closely related to being autistic.'),
('Autogender', 'Having a gender experience that is deeply connected and personal to oneself.'),
('Axigender', 'A gender identity that is between the two extremes of agender and any other type of gender. Both the genders are experienced one at a time without any overlapping. The two genders are described as on the opposite ends of an axis.'),
('Bigender', 'Having two gender identities at the same or different times.'),
('Biogender', 'Having a gender that is closely related to nature.'),
('Blurgender', 'Also called gender fuss, blurgender means having more than one gender identities that blur into each other so that no particular type of gender identity is clear.'),
('Boyflux', 'The person identifies themselves as male, but they experience varying degrees of male identity. This may range from feeling agender to completely male.'),
('Burstgender', 'Frequent bursts of intense feelings quickly move to the initial calm stage.'),
('Caelgender', 'This gender identity shares the qualities or aesthetics of outer space.'),
('Cassgender', 'It is associated with the feelings of considering the gender irrelevant or unimportant.'),
('Cassflux', 'There is a fluctuating intensity of irrelevance toward gender.'),
('Cavusgender', 'The person feels close to one gender when depressed and to another when not depressed.'),
('Cendgender', 'The gender identity changes from one gender to its opposite.'),
('Ceterogender', 'It is a nonbinary gender where the person has a specific masculine, feminine or neutral feelings.'),
('Ceterofluid', 'Although the person is a ceterogender, their identity keeps fluctuating between different genders.'),
('Cisgender', 'Being closely related to the gender assigned at birth during the entire life.'),
('Cloudgender', 'The person''s gender cannot be comprehended or understood due to depersonalization and derealization disorder.'),
('Collgender', 'Various genders are present at the same time in the individual.'),
('Colorgender', 'In this category, colors are used to describe gender, for example, pink gender or black gender.'),
('Commogender', 'The person knows that they are not cisgender yet continues to identify as one for a while.'),
('Condigender', 'The person feels their gender only under specific circumstances.'),
('Deliciagender', 'Associated with the feeling of having multiple genders but preferring one over the other.'),
('Demifluid', 'Having multiple genders, some fluid while others are static.'),
('Demiflux', 'A combination of multiple genders with some genders static, whereas others fluctuating in intensity.'),
('Demigender', 'The individual has partial traits of one gender and the rest of the other gender.'),
('Domgender', 'The individual has multiple genders with one dominating over the rest.'),
('Duragender', 'Having more than one gender with one lasting longer than the others.'),
('Egogender', 'It is a personal type of gender identified by the individual alone. It is based on the person''s experience within the self.'),
('Epicene', 'It is associated with a strong feeling of not being able to relate to any of the two genders of the binary gender or both of the binary gender characteristics.'),
('Esspigender', 'The individual relates their gender identity with spirits.'),
('Exgender', 'The denial to identify with any gender on the gender spectrum.'),
('Existigender', 'The person''s gender identity exists only when they make conscious efforts to realize it.'),
('Femfluid', 'The person is fluid or fluctuating regarding the feminine genders.'),
('Femgender', 'A nonbinary gender identity that is feminine.'),
('Fluidflux', 'It means to be fluid between two or more genders with a fluctuation in the intensity of those genders.'),
('Gemigender', 'The person has two genders that are opposite yet they flux and work together.'),
('Genderblank', 'It is closely related to a blank space.'),
('Genderflow', 'The gender identity is fluid between infinite feelings.'),
('Genderfluid', 'The person does not consistently adhere to one fixed gender and may have many genders.'),
('Genderfuzz', 'More than one gender is blurred together.'),
('Genderflux', 'The gender fluctuates in intensity.'),
('Genderpuck', 'The person resists to fit in societal norms concerning genders.'),
('Genderqueer', 'The individual blurs the preconceived boundaries of gender in relation to the gender binary or having just one gender type.'),
('Gender witched', 'The person is inclined toward the notion of having one gender but does not know which.'),
('Girlflux', 'The individual identifies themselves as a female but with varying intensities of female identities.'),
('Healgender', 'A gender identity that gives the person peace, calm, and positivity.'),
('Mirrorgender', 'Changing one''s gender type based on the people surrounding.'),
('Omnigender', 'Having or experiencing all genders.')
ON CONFLICT (name) DO NOTHING;