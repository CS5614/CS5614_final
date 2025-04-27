--RENTAL_LISTINGS
CREATE TABLE public.rental_listings (
    listing_db_id serial NOT NULL,
    listing_id text NOT NULL,
    listing_name text NULL,
    formatted_address text NULL,
    address_line_1 text NULL,
    address_line_2 text NULL,
    city text NULL,
    state character varying(2) NULL,
    zip_code character varying(10) NULL,
    county text NULL,
    latitude double precision NOT NULL,
    longitude double precision NOT NULL,
    geom geometry (Point, 4326) NULL,
    property_type text NULL,
    bedrooms integer NULL,
    bathrooms numeric(3, 1) NULL,
    square_footage integer NULL,
    year_built integer NULL,
    price integer NOT NULL,
    status text NULL,
    listing_type text NULL,
    listed_date timestamp with time zone NULL,
    last_seen_date timestamp with time zone NULL,
    removed_date timestamp with time zone NULL,
    created_date timestamp with time zone NULL,
    days_on_market integer NULL
);
ALTER TABLE public.rental_listings
ADD CONSTRAINT rental_listings_pkey PRIMARY KEY (listing_db_id);
--RENTAL_CLUSTERS
CREATE TABLE public.rental_clusters (
    cluster_id integer NOT NULL,
    centroid_lat double precision NOT NULL,
    centroid_lon double precision NOT NULL,
    member_count integer NOT NULL
);
ALTER TABLE public.rental_clusters
ADD CONSTRAINT rental_clusters_pkey PRIMARY KEY (cluster_id);
--PLACE_REVIEW
CREATE TABLE public.place_review (
    id serial NOT NULL,
    place_name character varying(255) NOT NULL,
    place_id character varying(255) NOT NULL,
    rating numeric(2, 1) NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    listing_id integer NOT NULL
);
ALTER TABLE public.place_review
ADD CONSTRAINT place_review_pkey PRIMARY KEY (id);
--OPEN_STREET
CREATE TABLE public.open_street (
    id serial NOT NULL,
    lat double precision NOT NULL,
    lon double precision NOT NULL,
    name text NULL,
    leisure text NULL,
    geom geometry (Point, 4326) NULL
);
ALTER TABLE public.open_street
ADD CONSTRAINT open_street_pkey PRIMARY KEY (id);
--LISTINGS_GEO
CREATE TABLE public.listings_geo (
    assignment_id serial NOT NULL,
    listing_db_id integer NOT NULL,
    geo_id text NOT NULL,
    assignment_date timestamp with time zone NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE public.listings_geo
ADD CONSTRAINT listings_geo_pkey PRIMARY KEY (assignment_id);
--LISTING_CLUSTERS
CREATE TABLE public.listing_clusters (
    assignment_id serial NOT NULL,
    listing_db_id integer NOT NULL,
    cluster_id integer NOT NULL
);
ALTER TABLE public.listing_clusters
ADD CONSTRAINT listing_clusters_pkey PRIMARY KEY (assignment_id);
--GEO_NWI
CREATE TABLE public.geo_nwi (
    geo_id text NOT NULL,
    nwi_score numeric(3, 1) NULL
);
ALTER TABLE public.geo_nwi
ADD CONSTRAINT geo_nwi_pkey PRIMARY KEY (geo_id);
--CRIME_REPORTS(deprecated)
CREATE TABLE public.crime_reports (
    id serial NOT NULL,
    name text NULL,
    date timestamp without time zone NULL,
    lat double precision NOT NULL,
    lon double precision NOT NULL,
    geom geometry (Point, 4326) NULL
);
ALTER TABLE public.crime_reports
ADD CONSTRAINT crime_reports_pkey PRIMARY KEY (id);
--CLUSTER_AIR_QUALITY
CREATE TABLE public.cluster_air_quality (
    aq_id serial NOT NULL,
    cluster_id integer NOT NULL,
    aqi integer NULL,
    category text NULL
);
ALTER TABLE public.cluster_air_quality
ADD CONSTRAINT cluster_air_quality_pkey PRIMARY KEY (aq_id);
--BUS_STOPS
CREATE TABLE public.bus_stops (
    id serial NOT NULL,
    name text NOT NULL,
    lon double precision NOT NULL,
    lat double precision NOT NULL,
    geom geometry (Point, 4326) NOT NULL
);
ALTER TABLE public.bus_stops
ADD CONSTRAINT bus_stops_pkey PRIMARY KEY (id);