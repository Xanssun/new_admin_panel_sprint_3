CREATE SCHEMA IF NOT EXISTS content;

CREATE TABLE IF NOT EXISTS content.film_work (
    id uuid PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    creation_date DATE,
    rating FLOAT,
    type TEXT NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);

CREATE TABLE IF NOT EXISTS content.person(
	id uuid PRIMARY KEY,
	full_name TEXT,
	created_at timestamp with time zone,
    updated_at timestamp with time zone
);

CREATE TABLE IF NOT EXISTS content.genre(
	id uuid PRIMARY KEY,
	name TEXT,
	description TEXT,
	created_at timestamp with time zone,
    updated_at timestamp with time zone
);

CREATE TABLE IF NOT EXISTS content.genre_film_work(
    id uuid PRIMARY KEY,
    genre_id uuid,
    film_work_id uuid,
    created_at timestamp with time zone,
    CONSTRAINT unique_genre_film_work UNIQUE (film_work_id, genre_id),
    FOREIGN KEY (genre_id) REFERENCES content.genre (id),
    FOREIGN KEY (film_work_id) REFERENCES content.film_work (id)
);

CREATE TABLE IF NOT EXISTS content.person_film_work(
    id uuid PRIMARY KEY,
    person_id uuid,
    film_work_id uuid,
    role TEXT,
    created_at timestamp with time zone,
    CONSTRAINT unique_person_film_work UNIQUE (film_work_id, person_id, role),
    FOREIGN KEY (person_id) REFERENCES content.person (id),
    FOREIGN KEY (film_work_id) REFERENCES content.film_work (id)
);

CREATE INDEX film_work_creation_date_idx ON content.film_work(creation_date);

CREATE UNIQUE INDEX film_work_person_role_idx ON content.person_film_work (film_work_id, person_id, role);

CREATE INDEX ON content.film_work (creation_date, rating);
