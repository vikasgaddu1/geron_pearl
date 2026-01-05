--
-- PostgreSQL database dump
--

-- Dumped from database version 17.2
-- Dumped by pg_dump version 17.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO postgres;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS '';


--
-- Name: authprovider; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.authprovider AS ENUM (
    'local',
    'google',
    'microsoft',
    'github',
    'okta',
    'custom'
);


ALTER TYPE public.authprovider OWNER TO postgres;

--
-- Name: textelementtype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.textelementtype AS ENUM (
    'title',
    'footnote',
    'population_set',
    'acronyms_set',
    'ich_category'
);


ALTER TYPE public.textelementtype OWNER TO postgres;

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.userrole AS ENUM (
    'ADMIN',
    'EDITOR',
    'VIEWER'
);


ALTER TYPE public.userrole OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: audit_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_log (
    id integer NOT NULL,
    table_name character varying(100) NOT NULL,
    record_id integer NOT NULL,
    action character varying(50) NOT NULL,
    user_id integer,
    changes_json text,
    ip_address character varying(45),
    user_agent text,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.audit_log OWNER TO postgres;

--
-- Name: audit_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.audit_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.audit_log_id_seq OWNER TO postgres;

--
-- Name: audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.audit_log_id_seq OWNED BY public.audit_log.id;


--
-- Name: database_releases; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.database_releases (
    id integer NOT NULL,
    study_id integer NOT NULL,
    database_release_label character varying(255) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.database_releases OWNER TO postgres;

--
-- Name: database_releases_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.database_releases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.database_releases_id_seq OWNER TO postgres;

--
-- Name: database_releases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.database_releases_id_seq OWNED BY public.database_releases.id;


--
-- Name: package_dataset_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.package_dataset_details (
    id integer NOT NULL,
    package_item_id integer NOT NULL,
    label character varying(255),
    sorting_order integer,
    acronyms text
);


ALTER TABLE public.package_dataset_details OWNER TO postgres;

--
-- Name: package_dataset_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.package_dataset_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.package_dataset_details_id_seq OWNER TO postgres;

--
-- Name: package_dataset_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.package_dataset_details_id_seq OWNED BY public.package_dataset_details.id;


--
-- Name: package_item_acronyms; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.package_item_acronyms (
    package_item_id integer NOT NULL,
    acronym_id integer NOT NULL
);


ALTER TABLE public.package_item_acronyms OWNER TO postgres;

--
-- Name: package_item_footnotes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.package_item_footnotes (
    package_item_id integer NOT NULL,
    footnote_id integer NOT NULL,
    sequence_number integer
);


ALTER TABLE public.package_item_footnotes OWNER TO postgres;

--
-- Name: package_items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.package_items (
    id integer NOT NULL,
    package_id integer NOT NULL,
    item_type character varying(7) NOT NULL,
    item_subtype character varying(50) NOT NULL,
    item_code character varying(255) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.package_items OWNER TO postgres;

--
-- Name: package_items_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.package_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.package_items_id_seq OWNER TO postgres;

--
-- Name: package_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.package_items_id_seq OWNED BY public.package_items.id;


--
-- Name: package_tlf_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.package_tlf_details (
    id integer NOT NULL,
    package_item_id integer NOT NULL,
    title_id integer,
    population_flag_id integer,
    ich_category_id integer
);


ALTER TABLE public.package_tlf_details OWNER TO postgres;

--
-- Name: package_tlf_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.package_tlf_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.package_tlf_details_id_seq OWNER TO postgres;

--
-- Name: package_tlf_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.package_tlf_details_id_seq OWNED BY public.package_tlf_details.id;


--
-- Name: packages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.packages (
    id integer NOT NULL,
    package_name character varying(255) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.packages OWNER TO postgres;

--
-- Name: packages_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.packages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.packages_id_seq OWNER TO postgres;

--
-- Name: packages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.packages_id_seq OWNED BY public.packages.id;


--
-- Name: reporting_effort_dataset_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reporting_effort_dataset_details (
    id integer NOT NULL,
    reporting_effort_item_id integer NOT NULL,
    label character varying(255),
    sorting_order integer,
    acronyms text
);


ALTER TABLE public.reporting_effort_dataset_details OWNER TO postgres;

--
-- Name: reporting_effort_dataset_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.reporting_effort_dataset_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reporting_effort_dataset_details_id_seq OWNER TO postgres;

--
-- Name: reporting_effort_dataset_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.reporting_effort_dataset_details_id_seq OWNED BY public.reporting_effort_dataset_details.id;


--
-- Name: reporting_effort_item_acronyms; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reporting_effort_item_acronyms (
    reporting_effort_item_id integer NOT NULL,
    acronym_id integer NOT NULL
);


ALTER TABLE public.reporting_effort_item_acronyms OWNER TO postgres;

--
-- Name: reporting_effort_item_footnotes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reporting_effort_item_footnotes (
    reporting_effort_item_id integer NOT NULL,
    footnote_id integer NOT NULL,
    sequence_number integer
);


ALTER TABLE public.reporting_effort_item_footnotes OWNER TO postgres;

--
-- Name: reporting_effort_item_tracker; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reporting_effort_item_tracker (
    id integer NOT NULL,
    reporting_effort_item_id integer NOT NULL,
    production_programmer_id integer,
    qc_programmer_id integer,
    production_status character varying(50) NOT NULL,
    qc_status character varying(50) NOT NULL,
    due_date date,
    qc_completion_date date,
    priority character varying(50) NOT NULL,
    qc_level character varying(50),
    in_production_flag boolean NOT NULL,
    unresolved_comment_count integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.reporting_effort_item_tracker OWNER TO postgres;

--
-- Name: reporting_effort_item_tracker_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.reporting_effort_item_tracker_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reporting_effort_item_tracker_id_seq OWNER TO postgres;

--
-- Name: reporting_effort_item_tracker_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.reporting_effort_item_tracker_id_seq OWNED BY public.reporting_effort_item_tracker.id;


--
-- Name: reporting_effort_items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reporting_effort_items (
    id integer NOT NULL,
    reporting_effort_id integer NOT NULL,
    source_type character varying(16),
    source_id integer,
    source_item_id integer,
    item_type character varying(7) NOT NULL,
    item_subtype character varying(50) NOT NULL,
    item_code character varying(255) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.reporting_effort_items OWNER TO postgres;

--
-- Name: reporting_effort_items_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.reporting_effort_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reporting_effort_items_id_seq OWNER TO postgres;

--
-- Name: reporting_effort_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.reporting_effort_items_id_seq OWNED BY public.reporting_effort_items.id;


--
-- Name: reporting_effort_tlf_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reporting_effort_tlf_details (
    id integer NOT NULL,
    reporting_effort_item_id integer NOT NULL,
    title_id integer,
    population_flag_id integer,
    ich_category_id integer
);


ALTER TABLE public.reporting_effort_tlf_details OWNER TO postgres;

--
-- Name: reporting_effort_tlf_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.reporting_effort_tlf_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reporting_effort_tlf_details_id_seq OWNER TO postgres;

--
-- Name: reporting_effort_tlf_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.reporting_effort_tlf_details_id_seq OWNED BY public.reporting_effort_tlf_details.id;


--
-- Name: reporting_efforts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reporting_efforts (
    id integer NOT NULL,
    study_id integer NOT NULL,
    database_release_id integer NOT NULL,
    database_release_label character varying(255) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.reporting_efforts OWNER TO postgres;

--
-- Name: reporting_efforts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.reporting_efforts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reporting_efforts_id_seq OWNER TO postgres;

--
-- Name: reporting_efforts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.reporting_efforts_id_seq OWNED BY public.reporting_efforts.id;


--
-- Name: studies; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.studies (
    id integer NOT NULL,
    study_label character varying(255) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.studies OWNER TO postgres;

--
-- Name: studies_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.studies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.studies_id_seq OWNER TO postgres;

--
-- Name: studies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.studies_id_seq OWNED BY public.studies.id;


--
-- Name: text_elements; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.text_elements (
    id integer NOT NULL,
    type public.textelementtype NOT NULL,
    label text NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.text_elements OWNER TO postgres;

--
-- Name: text_elements_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.text_elements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.text_elements_id_seq OWNER TO postgres;

--
-- Name: text_elements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.text_elements_id_seq OWNED BY public.text_elements.id;


--
-- Name: tracker_comments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tracker_comments (
    id integer NOT NULL,
    tracker_id integer NOT NULL,
    user_id integer NOT NULL,
    parent_comment_id integer,
    comment_text text NOT NULL,
    comment_type character varying(20) NOT NULL,
    is_resolved boolean NOT NULL,
    resolved_by_user_id integer,
    resolved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.tracker_comments OWNER TO postgres;

--
-- Name: tracker_comments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tracker_comments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tracker_comments_id_seq OWNER TO postgres;

--
-- Name: tracker_comments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tracker_comments_id_seq OWNED BY public.tracker_comments.id;


--
-- Name: tracker_item_tags; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tracker_item_tags (
    id integer NOT NULL,
    tracker_id integer NOT NULL,
    tag_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.tracker_item_tags OWNER TO postgres;

--
-- Name: tracker_item_tags_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tracker_item_tags_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tracker_item_tags_id_seq OWNER TO postgres;

--
-- Name: tracker_item_tags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tracker_item_tags_id_seq OWNED BY public.tracker_item_tags.id;


--
-- Name: tracker_status_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tracker_status_history (
    id integer NOT NULL,
    tracker_id integer NOT NULL,
    status_field character varying(20) NOT NULL,
    status_value character varying(50) NOT NULL,
    entered_at timestamp without time zone NOT NULL,
    exited_at timestamp without time zone,
    changed_by_user_id integer
);


ALTER TABLE public.tracker_status_history OWNER TO postgres;

--
-- Name: tracker_status_history_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tracker_status_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tracker_status_history_id_seq OWNER TO postgres;

--
-- Name: tracker_status_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tracker_status_history_id_seq OWNED BY public.tracker_status_history.id;


--
-- Name: tracker_tags; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tracker_tags (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    color character varying(7) NOT NULL,
    description text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.tracker_tags OWNER TO postgres;

--
-- Name: tracker_tags_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tracker_tags_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tracker_tags_id_seq OWNER TO postgres;

--
-- Name: tracker_tags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tracker_tags_id_seq OWNED BY public.tracker_tags.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying NOT NULL,
    email character varying,
    role public.userrole NOT NULL,
    department character varying(50),
    password_hash character varying,
    auth_provider public.authprovider NOT NULL,
    auth_provider_id character varying,
    is_active boolean NOT NULL,
    last_login_at timestamp without time zone,
    reset_token character varying,
    reset_token_expires timestamp without time zone,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: audit_log id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_log ALTER COLUMN id SET DEFAULT nextval('public.audit_log_id_seq'::regclass);


--
-- Name: database_releases id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.database_releases ALTER COLUMN id SET DEFAULT nextval('public.database_releases_id_seq'::regclass);


--
-- Name: package_dataset_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_dataset_details ALTER COLUMN id SET DEFAULT nextval('public.package_dataset_details_id_seq'::regclass);


--
-- Name: package_items id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_items ALTER COLUMN id SET DEFAULT nextval('public.package_items_id_seq'::regclass);


--
-- Name: package_tlf_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_tlf_details ALTER COLUMN id SET DEFAULT nextval('public.package_tlf_details_id_seq'::regclass);


--
-- Name: packages id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.packages ALTER COLUMN id SET DEFAULT nextval('public.packages_id_seq'::regclass);


--
-- Name: reporting_effort_dataset_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_dataset_details ALTER COLUMN id SET DEFAULT nextval('public.reporting_effort_dataset_details_id_seq'::regclass);


--
-- Name: reporting_effort_item_tracker id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_item_tracker ALTER COLUMN id SET DEFAULT nextval('public.reporting_effort_item_tracker_id_seq'::regclass);


--
-- Name: reporting_effort_items id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_items ALTER COLUMN id SET DEFAULT nextval('public.reporting_effort_items_id_seq'::regclass);


--
-- Name: reporting_effort_tlf_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_tlf_details ALTER COLUMN id SET DEFAULT nextval('public.reporting_effort_tlf_details_id_seq'::regclass);


--
-- Name: reporting_efforts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_efforts ALTER COLUMN id SET DEFAULT nextval('public.reporting_efforts_id_seq'::regclass);


--
-- Name: studies id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.studies ALTER COLUMN id SET DEFAULT nextval('public.studies_id_seq'::regclass);


--
-- Name: text_elements id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.text_elements ALTER COLUMN id SET DEFAULT nextval('public.text_elements_id_seq'::regclass);


--
-- Name: tracker_comments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tracker_comments ALTER COLUMN id SET DEFAULT nextval('public.tracker_comments_id_seq'::regclass);


--
-- Name: tracker_item_tags id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tracker_item_tags ALTER COLUMN id SET DEFAULT nextval('public.tracker_item_tags_id_seq'::regclass);


--
-- Name: tracker_status_history id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tracker_status_history ALTER COLUMN id SET DEFAULT nextval('public.tracker_status_history_id_seq'::regclass);


--
-- Name: tracker_tags id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tracker_tags ALTER COLUMN id SET DEFAULT nextval('public.tracker_tags_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
df7267a2f25d
\.


--
-- Data for Name: audit_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.audit_log (id, table_name, record_id, action, user_id, changes_json, ip_address, user_agent, created_at) FROM stdin;
\.


--
-- Data for Name: database_releases; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.database_releases (id, study_id, database_release_label, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: package_dataset_details; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.package_dataset_details (id, package_item_id, label, sorting_order, acronyms) FROM stdin;
\.


--
-- Data for Name: package_item_acronyms; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.package_item_acronyms (package_item_id, acronym_id) FROM stdin;
\.


--
-- Data for Name: package_item_footnotes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.package_item_footnotes (package_item_id, footnote_id, sequence_number) FROM stdin;
\.


--
-- Data for Name: package_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.package_items (id, package_id, item_type, item_subtype, item_code, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: package_tlf_details; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.package_tlf_details (id, package_item_id, title_id, population_flag_id, ich_category_id) FROM stdin;
\.


--
-- Data for Name: packages; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.packages (id, package_name, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: reporting_effort_dataset_details; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_effort_dataset_details (id, reporting_effort_item_id, label, sorting_order, acronyms) FROM stdin;
\.


--
-- Data for Name: reporting_effort_item_acronyms; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_effort_item_acronyms (reporting_effort_item_id, acronym_id) FROM stdin;
\.


--
-- Data for Name: reporting_effort_item_footnotes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_effort_item_footnotes (reporting_effort_item_id, footnote_id, sequence_number) FROM stdin;
\.


--
-- Data for Name: reporting_effort_item_tracker; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_effort_item_tracker (id, reporting_effort_item_id, production_programmer_id, qc_programmer_id, production_status, qc_status, due_date, qc_completion_date, priority, qc_level, in_production_flag, unresolved_comment_count, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: reporting_effort_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_effort_items (id, reporting_effort_id, source_type, source_id, source_item_id, item_type, item_subtype, item_code, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: reporting_effort_tlf_details; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_effort_tlf_details (id, reporting_effort_item_id, title_id, population_flag_id, ich_category_id) FROM stdin;
\.


--
-- Data for Name: reporting_efforts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_efforts (id, study_id, database_release_id, database_release_label, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: studies; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.studies (id, study_label, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: text_elements; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.text_elements (id, type, label, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tracker_comments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tracker_comments (id, tracker_id, user_id, parent_comment_id, comment_text, comment_type, is_resolved, resolved_by_user_id, resolved_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tracker_item_tags; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tracker_item_tags (id, tracker_id, tag_id, created_at) FROM stdin;
\.


--
-- Data for Name: tracker_status_history; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tracker_status_history (id, tracker_id, status_field, status_value, entered_at, exited_at, changed_by_user_id) FROM stdin;
\.


--
-- Data for Name: tracker_tags; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tracker_tags (id, name, color, description, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, email, role, department, password_hash, auth_provider, auth_provider_id, is_active, last_login_at, reset_token, reset_token_expires, created_at, updated_at) FROM stdin;
1	admin	admin@example.com	ADMIN	\N	$2b$12$WRyulLMOxYU1TeOQ/FvSm.B6oZ4q/ViuMA.5RAjsAFcdDIdLI/3xm	local	\N	t	2026-01-05 16:55:31.518953	\N	\N	2026-01-05 16:52:36.995723	2026-01-05 16:55:31.518953
\.


--
-- Name: audit_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.audit_log_id_seq', 1, false);


--
-- Name: database_releases_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.database_releases_id_seq', 1, false);


--
-- Name: package_dataset_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.package_dataset_details_id_seq', 1, false);


--
-- Name: package_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.package_items_id_seq', 1, false);


--
-- Name: package_tlf_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.package_tlf_details_id_seq', 1, false);


--
-- Name: packages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.packages_id_seq', 1, false);


--
-- Name: reporting_effort_dataset_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reporting_effort_dataset_details_id_seq', 1, false);


--
-- Name: reporting_effort_item_tracker_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reporting_effort_item_tracker_id_seq', 1, false);


--
-- Name: reporting_effort_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reporting_effort_items_id_seq', 1, false);


--
-- Name: reporting_effort_tlf_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reporting_effort_tlf_details_id_seq', 1, false);


--
-- Name: reporting_efforts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reporting_efforts_id_seq', 1, false);


--
-- Name: studies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.studies_id_seq', 1, false);


--
-- Name: text_elements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.text_elements_id_seq', 1, false);


--
-- Name: tracker_comments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tracker_comments_id_seq', 1, false);


--
-- Name: tracker_item_tags_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tracker_item_tags_id_seq', 1, false);


--
-- Name: tracker_status_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tracker_status_history_id_seq', 1, false);


--
-- Name: tracker_tags_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tracker_tags_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


--
-- Name: database_releases database_releases_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.database_releases
    ADD CONSTRAINT database_releases_pkey PRIMARY KEY (id);


--
-- Name: package_dataset_details package_dataset_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_dataset_details
    ADD CONSTRAINT package_dataset_details_pkey PRIMARY KEY (id);


--
-- Name: package_item_acronyms package_item_acronyms_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_item_acronyms
    ADD CONSTRAINT package_item_acronyms_pkey PRIMARY KEY (package_item_id, acronym_id);


--
-- Name: package_item_footnotes package_item_footnotes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_item_footnotes
    ADD CONSTRAINT package_item_footnotes_pkey PRIMARY KEY (package_item_id, footnote_id);


--
-- Name: package_items package_items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_items
    ADD CONSTRAINT package_items_pkey PRIMARY KEY (id);


--
-- Name: package_tlf_details package_tlf_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_tlf_details
    ADD CONSTRAINT package_tlf_details_pkey PRIMARY KEY (id);


--
-- Name: packages packages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.packages
    ADD CONSTRAINT packages_pkey PRIMARY KEY (id);


--
-- Name: reporting_effort_dataset_details reporting_effort_dataset_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_dataset_details
    ADD CONSTRAINT reporting_effort_dataset_details_pkey PRIMARY KEY (id);


--
-- Name: reporting_effort_item_acronyms reporting_effort_item_acronyms_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_item_acronyms
    ADD CONSTRAINT reporting_effort_item_acronyms_pkey PRIMARY KEY (reporting_effort_item_id, acronym_id);


--
-- Name: reporting_effort_item_footnotes reporting_effort_item_footnotes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_item_footnotes
    ADD CONSTRAINT reporting_effort_item_footnotes_pkey PRIMARY KEY (reporting_effort_item_id, footnote_id);


--
-- Name: reporting_effort_item_tracker reporting_effort_item_tracker_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_item_tracker
    ADD CONSTRAINT reporting_effort_item_tracker_pkey PRIMARY KEY (id);


--
-- Name: reporting_effort_items reporting_effort_items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_items
    ADD CONSTRAINT reporting_effort_items_pkey PRIMARY KEY (id);


--
-- Name: reporting_effort_tlf_details reporting_effort_tlf_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_tlf_details
    ADD CONSTRAINT reporting_effort_tlf_details_pkey PRIMARY KEY (id);


--
-- Name: reporting_efforts reporting_efforts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_efforts
    ADD CONSTRAINT reporting_efforts_pkey PRIMARY KEY (id);


--
-- Name: studies studies_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.studies
    ADD CONSTRAINT studies_pkey PRIMARY KEY (id);


--
-- Name: text_elements text_elements_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.text_elements
    ADD CONSTRAINT text_elements_pkey PRIMARY KEY (id);


--
-- Name: tracker_comments tracker_comments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tracker_comments
    ADD CONSTRAINT tracker_comments_pkey PRIMARY KEY (id);


--
-- Name: tracker_item_tags tracker_item_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tracker_item_tags
    ADD CONSTRAINT tracker_item_tags_pkey PRIMARY KEY (id);


--
-- Name: tracker_status_history tracker_status_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tracker_status_history
    ADD CONSTRAINT tracker_status_history_pkey PRIMARY KEY (id);


--
-- Name: tracker_tags tracker_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tracker_tags
    ADD CONSTRAINT tracker_tags_pkey PRIMARY KEY (id);


--
-- Name: reporting_efforts uq_database_release_reporting_effort_label; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_efforts
    ADD CONSTRAINT uq_database_release_reporting_effort_label UNIQUE (database_release_id, database_release_label);


--
-- Name: package_items uq_package_item_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_items
    ADD CONSTRAINT uq_package_item_unique UNIQUE (package_id, item_type, item_subtype, item_code);


--
-- Name: reporting_effort_items uq_reporting_effort_item_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_items
    ADD CONSTRAINT uq_reporting_effort_item_unique UNIQUE (reporting_effort_id, item_type, item_subtype, item_code);


--
-- Name: database_releases uq_study_database_release_label; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.database_releases
    ADD CONSTRAINT uq_study_database_release_label UNIQUE (study_id, database_release_label);


--
-- Name: reporting_effort_item_tracker uq_tracker_item; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_item_tracker
    ADD CONSTRAINT uq_tracker_item UNIQUE (reporting_effort_item_id);


--
-- Name: tracker_item_tags uq_tracker_tag; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tracker_item_tags
    ADD CONSTRAINT uq_tracker_tag UNIQUE (tracker_id, tag_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_audit_log_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_log_created_at ON public.audit_log USING btree (created_at);


--
-- Name: ix_audit_log_record_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_log_record_id ON public.audit_log USING btree (record_id);


--
-- Name: ix_audit_log_table_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_log_table_name ON public.audit_log USING btree (table_name);


--
-- Name: ix_audit_log_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_log_user_id ON public.audit_log USING btree (user_id);


--
-- Name: ix_database_releases_database_release_label; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_database_releases_database_release_label ON public.database_releases USING btree (database_release_label);


--
-- Name: ix_database_releases_study_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_database_releases_study_id ON public.database_releases USING btree (study_id);


--
-- Name: ix_package_dataset_details_package_item_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_package_dataset_details_package_item_id ON public.package_dataset_details USING btree (package_item_id);


--
-- Name: ix_package_items_item_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_package_items_item_type ON public.package_items USING btree (item_type);


--
-- Name: ix_package_items_package_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_package_items_package_id ON public.package_items USING btree (package_id);


--
-- Name: ix_package_tlf_details_package_item_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_package_tlf_details_package_item_id ON public.package_tlf_details USING btree (package_item_id);


--
-- Name: ix_packages_package_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_packages_package_name ON public.packages USING btree (package_name);


--
-- Name: ix_reporting_effort_dataset_details_reporting_effort_item_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_reporting_effort_dataset_details_reporting_effort_item_id ON public.reporting_effort_dataset_details USING btree (reporting_effort_item_id);


--
-- Name: ix_reporting_effort_item_tracker_production_programmer_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_reporting_effort_item_tracker_production_programmer_id ON public.reporting_effort_item_tracker USING btree (production_programmer_id);


--
-- Name: ix_reporting_effort_item_tracker_qc_programmer_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_reporting_effort_item_tracker_qc_programmer_id ON public.reporting_effort_item_tracker USING btree (qc_programmer_id);


--
-- Name: ix_reporting_effort_item_tracker_reporting_effort_item_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_reporting_effort_item_tracker_reporting_effort_item_id ON public.reporting_effort_item_tracker USING btree (reporting_effort_item_id);


--
-- Name: ix_reporting_effort_item_tracker_unresolved_comment_count; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_reporting_effort_item_tracker_unresolved_comment_count ON public.reporting_effort_item_tracker USING btree (unresolved_comment_count);


--
-- Name: ix_reporting_effort_items_item_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_reporting_effort_items_item_type ON public.reporting_effort_items USING btree (item_type);


--
-- Name: ix_reporting_effort_items_reporting_effort_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_reporting_effort_items_reporting_effort_id ON public.reporting_effort_items USING btree (reporting_effort_id);


--
-- Name: ix_reporting_effort_tlf_details_reporting_effort_item_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_reporting_effort_tlf_details_reporting_effort_item_id ON public.reporting_effort_tlf_details USING btree (reporting_effort_item_id);


--
-- Name: ix_reporting_efforts_database_release_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_reporting_efforts_database_release_id ON public.reporting_efforts USING btree (database_release_id);


--
-- Name: ix_reporting_efforts_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_reporting_efforts_id ON public.reporting_efforts USING btree (id);


--
-- Name: ix_reporting_efforts_study_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_reporting_efforts_study_id ON public.reporting_efforts USING btree (study_id);


--
-- Name: ix_studies_study_label; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_studies_study_label ON public.studies USING btree (study_label);


--
-- Name: ix_text_elements_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_text_elements_type ON public.text_elements USING btree (type);


--
-- Name: ix_tracker_comments_comment_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tracker_comments_comment_type ON public.tracker_comments USING btree (comment_type);


--
-- Name: ix_tracker_comments_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tracker_comments_created_at ON public.tracker_comments USING btree (created_at);


--
-- Name: ix_tracker_comments_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tracker_comments_id ON public.tracker_comments USING btree (id);


--
-- Name: ix_tracker_comments_is_resolved; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tracker_comments_is_resolved ON public.tracker_comments USING btree (is_resolved);


--
-- Name: ix_tracker_comments_parent_comment_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tracker_comments_parent_comment_id ON public.tracker_comments USING btree (parent_comment_id);


--
-- Name: ix_tracker_comments_tracker_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tracker_comments_tracker_id ON public.tracker_comments USING btree (tracker_id);


--
-- Name: ix_tracker_comments_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tracker_comments_user_id ON public.tracker_comments USING btree (user_id);


--
-- Name: ix_tracker_item_tags_tag_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tracker_item_tags_tag_id ON public.tracker_item_tags USING btree (tag_id);


--
-- Name: ix_tracker_item_tags_tracker_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tracker_item_tags_tracker_id ON public.tracker_item_tags USING btree (tracker_id);


--
-- Name: ix_tracker_status_history_entered_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tracker_status_history_entered_at ON public.tracker_status_history USING btree (entered_at);


--
-- Name: ix_tracker_status_history_tracker_field; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tracker_status_history_tracker_field ON public.tracker_status_history USING btree (tracker_id, status_field);


--
-- Name: ix_tracker_status_history_tracker_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tracker_status_history_tracker_id ON public.tracker_status_history USING btree (tracker_id);


--
-- Name: ix_tracker_tags_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_tracker_tags_name ON public.tracker_tags USING btree (name);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: audit_log audit_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: database_releases database_releases_study_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.database_releases
    ADD CONSTRAINT database_releases_study_id_fkey FOREIGN KEY (study_id) REFERENCES public.studies(id);


--
-- Name: package_dataset_details package_dataset_details_package_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_dataset_details
    ADD CONSTRAINT package_dataset_details_package_item_id_fkey FOREIGN KEY (package_item_id) REFERENCES public.package_items(id);


--
-- Name: package_item_acronyms package_item_acronyms_acronym_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_item_acronyms
    ADD CONSTRAINT package_item_acronyms_acronym_id_fkey FOREIGN KEY (acronym_id) REFERENCES public.text_elements(id);


--
-- Name: package_item_acronyms package_item_acronyms_package_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_item_acronyms
    ADD CONSTRAINT package_item_acronyms_package_item_id_fkey FOREIGN KEY (package_item_id) REFERENCES public.package_items(id);


--
-- Name: package_item_footnotes package_item_footnotes_footnote_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_item_footnotes
    ADD CONSTRAINT package_item_footnotes_footnote_id_fkey FOREIGN KEY (footnote_id) REFERENCES public.text_elements(id);


--
-- Name: package_item_footnotes package_item_footnotes_package_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_item_footnotes
    ADD CONSTRAINT package_item_footnotes_package_item_id_fkey FOREIGN KEY (package_item_id) REFERENCES public.package_items(id);


--
-- Name: package_items package_items_package_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_items
    ADD CONSTRAINT package_items_package_id_fkey FOREIGN KEY (package_id) REFERENCES public.packages(id);


--
-- Name: package_tlf_details package_tlf_details_ich_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_tlf_details
    ADD CONSTRAINT package_tlf_details_ich_category_id_fkey FOREIGN KEY (ich_category_id) REFERENCES public.text_elements(id);


--
-- Name: package_tlf_details package_tlf_details_package_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_tlf_details
    ADD CONSTRAINT package_tlf_details_package_item_id_fkey FOREIGN KEY (package_item_id) REFERENCES public.package_items(id);


--
-- Name: package_tlf_details package_tlf_details_population_flag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_tlf_details
    ADD CONSTRAINT package_tlf_details_population_flag_id_fkey FOREIGN KEY (population_flag_id) REFERENCES public.text_elements(id);


--
-- Name: package_tlf_details package_tlf_details_title_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_tlf_details
    ADD CONSTRAINT package_tlf_details_title_id_fkey FOREIGN KEY (title_id) REFERENCES public.text_elements(id);


--
-- Name: reporting_effort_dataset_details reporting_effort_dataset_details_reporting_effort_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_dataset_details
    ADD CONSTRAINT reporting_effort_dataset_details_reporting_effort_item_id_fkey FOREIGN KEY (reporting_effort_item_id) REFERENCES public.reporting_effort_items(id);


--
-- Name: reporting_effort_item_acronyms reporting_effort_item_acronyms_acronym_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_item_acronyms
    ADD CONSTRAINT reporting_effort_item_acronyms_acronym_id_fkey FOREIGN KEY (acronym_id) REFERENCES public.text_elements(id);


--
-- Name: reporting_effort_item_acronyms reporting_effort_item_acronyms_reporting_effort_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_item_acronyms
    ADD CONSTRAINT reporting_effort_item_acronyms_reporting_effort_item_id_fkey FOREIGN KEY (reporting_effort_item_id) REFERENCES public.reporting_effort_items(id);


--
-- Name: reporting_effort_item_footnotes reporting_effort_item_footnotes_footnote_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_item_footnotes
    ADD CONSTRAINT reporting_effort_item_footnotes_footnote_id_fkey FOREIGN KEY (footnote_id) REFERENCES public.text_elements(id);


--
-- Name: reporting_effort_item_footnotes reporting_effort_item_footnotes_reporting_effort_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_item_footnotes
    ADD CONSTRAINT reporting_effort_item_footnotes_reporting_effort_item_id_fkey FOREIGN KEY (reporting_effort_item_id) REFERENCES public.reporting_effort_items(id);


--
-- Name: reporting_effort_item_tracker reporting_effort_item_tracker_production_programmer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_item_tracker
    ADD CONSTRAINT reporting_effort_item_tracker_production_programmer_id_fkey FOREIGN KEY (production_programmer_id) REFERENCES public.users(id);


--
-- Name: reporting_effort_item_tracker reporting_effort_item_tracker_qc_programmer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_item_tracker
    ADD CONSTRAINT reporting_effort_item_tracker_qc_programmer_id_fkey FOREIGN KEY (qc_programmer_id) REFERENCES public.users(id);


--
-- Name: reporting_effort_item_tracker reporting_effort_item_tracker_reporting_effort_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_item_tracker
    ADD CONSTRAINT reporting_effort_item_tracker_reporting_effort_item_id_fkey FOREIGN KEY (reporting_effort_item_id) REFERENCES public.reporting_effort_items(id);


--
-- Name: reporting_effort_items reporting_effort_items_reporting_effort_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_items
    ADD CONSTRAINT reporting_effort_items_reporting_effort_id_fkey FOREIGN KEY (reporting_effort_id) REFERENCES public.reporting_efforts(id);


--
-- Name: reporting_effort_tlf_details reporting_effort_tlf_details_ich_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_tlf_details
    ADD CONSTRAINT reporting_effort_tlf_details_ich_category_id_fkey FOREIGN KEY (ich_category_id) REFERENCES public.text_elements(id);


--
-- Name: reporting_effort_tlf_details reporting_effort_tlf_details_population_flag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_tlf_details
    ADD CONSTRAINT reporting_effort_tlf_details_population_flag_id_fkey FOREIGN KEY (population_flag_id) REFERENCES public.text_elements(id);


--
-- Name: reporting_effort_tlf_details reporting_effort_tlf_details_reporting_effort_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_tlf_details
    ADD CONSTRAINT reporting_effort_tlf_details_reporting_effort_item_id_fkey FOREIGN KEY (reporting_effort_item_id) REFERENCES public.reporting_effort_items(id);


--
-- Name: reporting_effort_tlf_details reporting_effort_tlf_details_title_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_tlf_details
    ADD CONSTRAINT reporting_effort_tlf_details_title_id_fkey FOREIGN KEY (title_id) REFERENCES public.text_elements(id);


--
-- Name: reporting_efforts reporting_efforts_database_release_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_efforts
    ADD CONSTRAINT reporting_efforts_database_release_id_fkey FOREIGN KEY (database_release_id) REFERENCES public.database_releases(id);


--
-- Name: reporting_efforts reporting_efforts_study_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_efforts
    ADD CONSTRAINT reporting_efforts_study_id_fkey FOREIGN KEY (study_id) REFERENCES public.studies(id);


--
-- Name: tracker_comments tracker_comments_parent_comment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tracker_comments
    ADD CONSTRAINT tracker_comments_parent_comment_id_fkey FOREIGN KEY (parent_comment_id) REFERENCES public.tracker_comments(id) ON DELETE CASCADE;


--
-- Name: tracker_comments tracker_comments_resolved_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tracker_comments
    ADD CONSTRAINT tracker_comments_resolved_by_user_id_fkey FOREIGN KEY (resolved_by_user_id) REFERENCES public.users(id);


--
-- Name: tracker_comments tracker_comments_tracker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tracker_comments
    ADD CONSTRAINT tracker_comments_tracker_id_fkey FOREIGN KEY (tracker_id) REFERENCES public.reporting_effort_item_tracker(id) ON DELETE CASCADE;


--
-- Name: tracker_comments tracker_comments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tracker_comments
    ADD CONSTRAINT tracker_comments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: tracker_item_tags tracker_item_tags_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tracker_item_tags
    ADD CONSTRAINT tracker_item_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tracker_tags(id) ON DELETE CASCADE;


--
-- Name: tracker_item_tags tracker_item_tags_tracker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tracker_item_tags
    ADD CONSTRAINT tracker_item_tags_tracker_id_fkey FOREIGN KEY (tracker_id) REFERENCES public.reporting_effort_item_tracker(id) ON DELETE CASCADE;


--
-- Name: tracker_status_history tracker_status_history_changed_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tracker_status_history
    ADD CONSTRAINT tracker_status_history_changed_by_user_id_fkey FOREIGN KEY (changed_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: tracker_status_history tracker_status_history_tracker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tracker_status_history
    ADD CONSTRAINT tracker_status_history_tracker_id_fkey FOREIGN KEY (tracker_id) REFERENCES public.reporting_effort_item_tracker(id) ON DELETE CASCADE;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

