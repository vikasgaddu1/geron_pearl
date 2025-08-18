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
-- Name: commenttype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.commenttype AS ENUM (
    'qc_comment',
    'prod_comment',
    'biostat_comment'
);


ALTER TYPE public.commenttype OWNER TO postgres;

--
-- Name: itemtype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.itemtype AS ENUM (
    'TLF',
    'Dataset'
);


ALTER TYPE public.itemtype OWNER TO postgres;

--
-- Name: sourcetype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.sourcetype AS ENUM (
    'package',
    'reporting_effort',
    'custom',
    'bulk_upload'
);


ALTER TYPE public.sourcetype OWNER TO postgres;

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
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
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
    production_status character varying(50) NOT NULL,
    due_date date,
    priority character varying(50) NOT NULL,
    qc_level character varying(50),
    qc_programmer_id integer,
    qc_status character varying(50) NOT NULL,
    qc_completion_date date,
    in_production_flag boolean NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    unresolved_comment_count integer DEFAULT 0 NOT NULL
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
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
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
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(100) NOT NULL,
    role public.userrole NOT NULL,
    department character varying(50)
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
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
f5a535fcf5e5
\.


--
-- Data for Name: audit_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.audit_log (id, table_name, record_id, action, user_id, changes_json, ip_address, user_agent, created_at) FROM stdin;
1	reporting_effort_items	2	CREATE	\N	{"created": {"id": 2, "reporting_effort_id": 2, "source_type": null, "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_TEST_001", "is_active": true, "created_at": "2025-08-13T21:04:02.355855", "updated_at": "2025-08-13T21:04:02.355855"}}	127.0.0.1	Python-urllib/3.11	2025-08-13 21:04:02.413893
2	reporting_effort_items	5	CREATE	\N	{"created": {"id": 5, "reporting_effort_id": 2, "source_type": null, "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_VERIFY_002", "is_active": true, "created_at": "2025-08-13T21:11:25.854159", "updated_at": "2025-08-13T21:11:25.854159"}}	127.0.0.1	Python-urllib/3.11	2025-08-13 21:11:25.896036
3	reporting_effort_items	7	CREATE	\N	{"created": {"id": 7, "reporting_effort_id": 2, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_API_CHECK_003", "is_active": true, "created_at": "2025-08-13T21:26:20.756582", "updated_at": "2025-08-13T21:26:20.756582"}}	127.0.0.1	Python-urllib/3.11	2025-08-13 21:26:20.805073
4	reporting_effort_items	8	CREATE	\N	{"created": {"id": 8, "reporting_effort_id": 2, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_TEST_FIXED", "is_active": true, "created_at": "2025-08-13T21:36:36.005737", "updated_at": "2025-08-13T21:36:36.005737"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:36:36.059223
5	reporting_effort_items	9	CREATE	\N	{"created": {"id": 9, "reporting_effort_id": 11, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_14_1_1", "is_active": true, "created_at": "2025-08-13T21:36:44.662762", "updated_at": "2025-08-13T21:36:44.662762"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:36:44.682879
6	reporting_effort_items	10	CREATE	\N	{"created": {"id": 10, "reporting_effort_id": 11, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "Dataset", "item_subtype": "ADaM", "item_code": "ADSL", "is_active": true, "created_at": "2025-08-13T21:36:44.800997", "updated_at": "2025-08-13T21:36:44.800997"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:36:44.82438
7	reporting_effort_items	11	CREATE	\N	{"created": {"id": 11, "reporting_effort_id": 11, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_2", "is_active": true, "created_at": "2025-08-13T21:36:45.676049", "updated_at": "2025-08-13T21:36:45.676049"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:36:45.69133
8	reporting_effort_items	12	CREATE	\N	{"created": {"id": 12, "reporting_effort_id": 11, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_3", "is_active": true, "created_at": "2025-08-13T21:36:45.745277", "updated_at": "2025-08-13T21:36:45.745277"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:36:45.760875
9	reporting_effort_items	13	CREATE	\N	{"created": {"id": 13, "reporting_effort_id": 11, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_4", "is_active": true, "created_at": "2025-08-13T21:36:45.812912", "updated_at": "2025-08-13T21:36:45.812912"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:36:45.82832
10	reporting_effort_items	14	CREATE	\N	{"created": {"id": 14, "reporting_effort_id": 11, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_5", "is_active": true, "created_at": "2025-08-13T21:36:45.878209", "updated_at": "2025-08-13T21:36:45.878209"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:36:45.896283
11	reporting_effort_items	15	CREATE	\N	{"created": {"id": 15, "reporting_effort_id": 12, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_14_1_1", "is_active": true, "created_at": "2025-08-13T21:38:04.936951", "updated_at": "2025-08-13T21:38:04.936951"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:38:04.956484
12	reporting_effort_items	16	CREATE	\N	{"created": {"id": 16, "reporting_effort_id": 12, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "Dataset", "item_subtype": "ADaM", "item_code": "ADSL", "is_active": true, "created_at": "2025-08-13T21:38:05.059423", "updated_at": "2025-08-13T21:38:05.059423"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:38:05.088016
13	reporting_effort_items	17	CREATE	\N	{"created": {"id": 17, "reporting_effort_id": 12, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_2", "is_active": true, "created_at": "2025-08-13T21:38:05.907808", "updated_at": "2025-08-13T21:38:05.907808"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:38:05.926601
14	reporting_effort_items	18	CREATE	\N	{"created": {"id": 18, "reporting_effort_id": 12, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_3", "is_active": true, "created_at": "2025-08-13T21:38:05.986821", "updated_at": "2025-08-13T21:38:05.986821"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:38:05.999656
15	reporting_effort_items	19	CREATE	\N	{"created": {"id": 19, "reporting_effort_id": 12, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_4", "is_active": true, "created_at": "2025-08-13T21:38:06.044613", "updated_at": "2025-08-13T21:38:06.044613"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:38:06.064968
16	reporting_effort_items	20	CREATE	\N	{"created": {"id": 20, "reporting_effort_id": 12, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_5", "is_active": true, "created_at": "2025-08-13T21:38:06.145201", "updated_at": "2025-08-13T21:38:06.145201"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:38:06.158298
17	reporting_effort_items	21	CREATE	\N	{"created": {"id": 21, "reporting_effort_id": 13, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_DEBUG_1", "is_active": true, "created_at": "2025-08-13T21:38:56.166746", "updated_at": "2025-08-13T21:38:56.166746"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:38:56.193399
18	reporting_effort_items	23	CREATE	\N	{"created": {"id": 23, "reporting_effort_id": 13, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_DEBUG_1755121159", "is_active": true, "created_at": "2025-08-13T21:39:19.660966", "updated_at": "2025-08-13T21:39:19.660966"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:39:19.679723
19	reporting_effort_items	24	CREATE	\N	{"created": {"id": 24, "reporting_effort_id": 13, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_DEBUG_UNIQUE_1755121209", "is_active": true, "created_at": "2025-08-13T21:40:09.278340", "updated_at": "2025-08-13T21:40:09.278340"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:40:09.299518
20	reporting_effort_items	26	CREATE	\N	{"created": {"id": 26, "reporting_effort_id": 2, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_API_TEST_1755121286", "is_active": true, "created_at": "2025-08-13T21:41:26.978578", "updated_at": "2025-08-13T21:41:26.978578"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:41:26.992828
21	reporting_effort_items	27	CREATE	\N	{"created": {"id": 27, "reporting_effort_id": 2, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_DEBUG_1755121327", "is_active": true, "created_at": "2025-08-13T21:42:07.223666", "updated_at": "2025-08-13T21:42:07.223666"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:42:07.25935
22	reporting_effort_items	28	CREATE	\N	{"created": {"id": 28, "reporting_effort_id": 2, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_FIXED_1755121372", "is_active": true, "created_at": "2025-08-13T21:42:52.603785", "updated_at": "2025-08-13T21:42:52.603785"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:42:52.666991
23	reporting_effort_items	29	CREATE	\N	{"created": {"id": 29, "reporting_effort_id": 2, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_AFTER_RELOAD_1755121385", "is_active": true, "created_at": "2025-08-13T21:43:05.862559", "updated_at": "2025-08-13T21:43:05.862559"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:43:05.885118
24	reporting_effort_items	30	CREATE	\N	{"created": {"id": 30, "reporting_effort_id": 2, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_NO_WEBSOCKET_1755121419", "is_active": true, "created_at": "2025-08-13T21:43:39.843596", "updated_at": "2025-08-13T21:43:39.843596"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:43:39.895161
25	reporting_effort_items	36	DELETE	\N	{"deleted": {"id": 36, "reporting_effort_id": 14, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_14_1_1", "is_active": true, "created_at": "2025-08-13T21:46:39.940070", "updated_at": "2025-08-13T21:46:39.940070"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:46:40.879659
26	reporting_effort_items	37	DELETE	\N	{"deleted": {"id": 37, "reporting_effort_id": 14, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "Dataset", "item_subtype": "ADaM", "item_code": "ADSL", "is_active": true, "created_at": "2025-08-13T21:46:40.081505", "updated_at": "2025-08-13T21:46:40.081505"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:46:41.706792
27	reporting_effort_items	42	CREATE	\N	{"created": {"id": 42, "reporting_effort_id": 2, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_VERIFY_1755121764", "is_active": true, "created_at": "2025-08-13T21:49:24.734302", "updated_at": "2025-08-13T21:49:24.734302"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:49:24.80469
28	reporting_effort_items	43	CREATE	\N	{"created": {"id": 43, "reporting_effort_id": 15, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_14_1_1", "is_active": true, "created_at": "2025-08-13T21:51:23.206384", "updated_at": "2025-08-13T21:51:23.206384"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:51:23.246018
29	reporting_effort_items	44	CREATE	\N	{"created": {"id": 44, "reporting_effort_id": 15, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "Dataset", "item_subtype": "ADaM", "item_code": "ADSL", "is_active": true, "created_at": "2025-08-13T21:51:23.371517", "updated_at": "2025-08-13T21:51:23.371517"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:51:23.392499
30	reporting_effort_items	43	DELETE	\N	{"deleted": {"id": 43, "reporting_effort_id": 15, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_14_1_1", "is_active": true, "created_at": "2025-08-13T21:51:23.206384", "updated_at": "2025-08-13T21:51:23.206384"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:51:24.20871
31	reporting_effort_items	45	CREATE	\N	{"created": {"id": 45, "reporting_effort_id": 15, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_2", "is_active": true, "created_at": "2025-08-13T21:51:24.303649", "updated_at": "2025-08-13T21:51:24.303649"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:51:24.319655
32	reporting_effort_items	46	CREATE	\N	{"created": {"id": 46, "reporting_effort_id": 15, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_3", "is_active": true, "created_at": "2025-08-13T21:51:24.371505", "updated_at": "2025-08-13T21:51:24.371505"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:51:24.387518
33	reporting_effort_items	47	CREATE	\N	{"created": {"id": 47, "reporting_effort_id": 15, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_4", "is_active": true, "created_at": "2025-08-13T21:51:24.451623", "updated_at": "2025-08-13T21:51:24.451623"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:51:24.475688
34	reporting_effort_items	48	CREATE	\N	{"created": {"id": 48, "reporting_effort_id": 15, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_5", "is_active": true, "created_at": "2025-08-13T21:51:24.544739", "updated_at": "2025-08-13T21:51:24.544739"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:51:24.566759
35	reporting_effort_items	44	DELETE	\N	{"deleted": {"id": 44, "reporting_effort_id": 15, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "Dataset", "item_subtype": "ADaM", "item_code": "ADSL", "is_active": true, "created_at": "2025-08-13T21:51:23.371517", "updated_at": "2025-08-13T21:51:23.371517"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:51:25.081823
36	reporting_effort_items	49	CREATE	\N	{"created": {"id": 49, "reporting_effort_id": 16, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_14_1_1", "is_active": true, "created_at": "2025-08-13T21:52:10.549865", "updated_at": "2025-08-13T21:52:10.549865"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:52:10.592384
37	reporting_effort_items	50	CREATE	\N	{"created": {"id": 50, "reporting_effort_id": 16, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "Dataset", "item_subtype": "ADaM", "item_code": "ADSL", "is_active": true, "created_at": "2025-08-13T21:52:10.718663", "updated_at": "2025-08-13T21:52:10.718663"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:52:10.737553
38	reporting_effort_items	49	DELETE	\N	{"deleted": {"id": 49, "reporting_effort_id": 16, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_14_1_1", "is_active": true, "created_at": "2025-08-13T21:52:10.549865", "updated_at": "2025-08-13T21:52:10.549865"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:52:11.510717
39	reporting_effort_items	51	CREATE	\N	{"created": {"id": 51, "reporting_effort_id": 16, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_2", "is_active": true, "created_at": "2025-08-13T21:52:11.599386", "updated_at": "2025-08-13T21:52:11.599386"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:52:11.615976
40	reporting_effort_items	52	CREATE	\N	{"created": {"id": 52, "reporting_effort_id": 16, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_3", "is_active": true, "created_at": "2025-08-13T21:52:11.665996", "updated_at": "2025-08-13T21:52:11.665996"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:52:11.680972
41	reporting_effort_items	53	CREATE	\N	{"created": {"id": 53, "reporting_effort_id": 16, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_4", "is_active": true, "created_at": "2025-08-13T21:52:11.746648", "updated_at": "2025-08-13T21:52:11.746648"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:52:11.759663
42	reporting_effort_items	54	CREATE	\N	{"created": {"id": 54, "reporting_effort_id": 16, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_5", "is_active": true, "created_at": "2025-08-13T21:52:11.813845", "updated_at": "2025-08-13T21:52:11.813845"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:52:11.830845
43	reporting_effort_items	50	DELETE	\N	{"deleted": {"id": 50, "reporting_effort_id": 16, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "Dataset", "item_subtype": "ADaM", "item_code": "ADSL", "is_active": true, "created_at": "2025-08-13T21:52:10.718663", "updated_at": "2025-08-13T21:52:10.718663"}}	127.0.0.1	curl/7.87.0	2025-08-13 21:52:12.356835
44	reporting_effort_items	2	COPY_FROM_PACKAGE	\N	{"copy_operation": {"source_package_id": 3, "source_item_ids": null, "copied_count": 0, "created_item_ids": []}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 07:10:37.008626
45	reporting_effort_items	2	COPY_FROM_REPORTING_EFFORT	\N	{"copy_operation": {"source_reporting_effort_id": 5, "source_item_ids": null, "copied_count": 0, "created_item_ids": []}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 07:10:53.079332
46	reporting_effort_items	2	COPY_FROM_PACKAGE	\N	{"copy_operation": {"source_package_id": 1, "source_item_ids": null, "summary": {"total_attempted": 15, "created_count": 0, "skipped_count": 15, "success": true}, "created_item_ids": [], "skipped_items": [{"item_type": "TLF", "item_subtype": "Table", "item_code": "t14.1.1", "reason": "already_exists"}, {"item_type": "TLF", "item_subtype": "Table", "item_code": "t14.2.1", "reason": "already_exists"}, {"item_type": "TLF", "item_subtype": "Listing", "item_code": "l16.1.1", "reason": "already_exists"}, {"item_type": "Dataset", "item_subtype": "SDTM", "item_code": "DM", "reason": "already_exists"}, {"item_type": "Dataset", "item_subtype": "SDTM", "item_code": "ae", "reason": "already_exists"}, {"item_type": "Dataset", "item_subtype": "SDTM", "item_code": "vs", "reason": "already_exists"}, {"item_type": "Dataset", "item_subtype": "SDTM", "item_code": "lb", "reason": "already_exists"}, {"item_type": "Dataset", "item_subtype": "ADaM", "item_code": "adsl", "reason": "already_exists"}, {"item_type": "Dataset", "item_subtype": "ADaM", "item_code": "adae", "reason": "already_exists"}, {"item_type": "TLF", "item_subtype": "Table", "item_code": "t11", "reason": "already_exists"}, {"item_type": "Dataset", "item_subtype": "SDTM", "item_code": "cm", "reason": "already_exists"}, {"item_type": "Dataset", "item_subtype": "ADaM", "item_code": "adeff", "reason": "already_exists"}, {"item_type": "TLF", "item_subtype": "Figure", "item_code": "f9.1.1", "reason": "already_exists"}, {"item_type": "TLF", "item_subtype": "Table", "item_code": "t20.1.1", "reason": "already_exists"}, {"item_type": "TLF", "item_subtype": "Table", "item_code": "t99.9.9", "reason": "already_exists"}]}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 08:04:31.422418
47	reporting_effort_items	4	COPY_FROM_REPORTING_EFFORT	\N	{"copy_operation": {"source_reporting_effort_id": 2, "source_item_ids": null, "copied_count": 35, "created_item_ids": [71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105]}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 08:37:29.006239
48	reporting_effort_items	5	COPY_FROM_REPORTING_EFFORT	\N	{"copy_operation": {"source_reporting_effort_id": 2, "source_item_ids": null, "created_count": 35, "skipped_count": 0, "created_item_ids": [106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140], "skipped_items": []}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 08:41:51.862337
49	reporting_effort_items	5	COPY_FROM_REPORTING_EFFORT	\N	{"copy_operation": {"source_reporting_effort_id": 2, "source_item_ids": null, "created_count": 0, "skipped_count": 35, "created_item_ids": [], "skipped_items": [{"item_code": "adae", "item_type": "Dataset", "reason": "Duplicate item already exists"}, {"item_code": "adeff", "item_type": "Dataset", "reason": "Duplicate item already exists"}, {"item_code": "adsl", "item_type": "Dataset", "reason": "Duplicate item already exists"}, {"item_code": "ae", "item_type": "Dataset", "reason": "Duplicate item already exists"}, {"item_code": "cm", "item_type": "Dataset", "reason": "Duplicate item already exists"}, {"item_code": "DM", "item_type": "Dataset", "reason": "Duplicate item already exists"}, {"item_code": "f9.1.1", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "l16.1.1", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "lb", "item_type": "Dataset", "reason": "Duplicate item already exists"}, {"item_code": "T_14_1_1_DEBUG", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_AFTER_RELOAD_1755121385", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_API_CHECK_003", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_API_TEST_1755121286", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_CHECK_001", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_DEBUG_1755121327", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_DICT_RESPONSE_1755121577", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_DIRECT_TEST_88409.656", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_FIXED_1755121372", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_MINIMAL_1755121531", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_NO_AUDIT_1755121437", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_NO_WEBSOCKET_1755121419", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_SIMPLE_OBJECT_1755121502", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_SIMPLE_RESPONSE_1755121452", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_TEST_001", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_TEST_FINAL_001", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_TEST_FIXED", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_VERIFY_001", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_VERIFY_002", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "T_VERIFY_1755121764", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "t11", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "t14.1.1", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "t14.2.1", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "t20.1.1", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "t99.9.9", "item_type": "TLF", "reason": "Duplicate item already exists"}, {"item_code": "vs", "item_type": "Dataset", "reason": "Duplicate item already exists"}]}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 08:41:59.44465
50	reporting_effort_items	13	COPY_FROM_REPORTING_EFFORT	\N	{"copy_operation": {"source_reporting_effort_id": 2, "source_item_ids": null, "created_count": 35, "skipped_count": 0, "created_item_ids": [141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175], "skipped_items": []}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 08:43:41.043233
51	reporting_effort_items	5	COPY_FROM_REPORTING_EFFORT	\N	{"copy_operation": {"source_reporting_effort_id": 2, "source_item_ids": null, "created_count": 35, "skipped_count": 0, "created_item_ids": [176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210], "skipped_items": []}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 08:48:45.176389
52	reporting_effort_items	182	DELETE	\N	{"deleted": {"id": 182, "reporting_effort_id": 5, "source_type": "reporting_effort", "source_id": 2, "source_item_id": 68, "item_type": "TLF", "item_subtype": "Figure", "item_code": "f9.1.1", "is_active": true, "created_at": "2025-08-14T08:48:44.712876", "updated_at": "2025-08-14T08:48:44.712876"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 08:57:48.399272
53	reporting_effort_items	183	DELETE	\N	{"deleted": {"id": 183, "reporting_effort_id": 5, "source_type": "reporting_effort", "source_id": 2, "source_item_id": 58, "item_type": "TLF", "item_subtype": "Listing", "item_code": "l16.1.1", "is_active": true, "created_at": "2025-08-14T08:48:44.728295", "updated_at": "2025-08-14T08:48:44.728295"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 08:57:51.131501
54	reporting_effort_items	5	COPY_FROM_REPORTING_EFFORT	\N	{"copy_operation": {"source_reporting_effort_id": 2, "source_item_ids": null, "created_count": 2, "skipped_count": 33, "created_item_ids": [211, 212], "skipped_items": [{"item_code": "adae", "item_type": "Dataset", "item_subtype": "ADaM", "reason": "Duplicate item already exists"}, {"item_code": "adeff", "item_type": "Dataset", "item_subtype": "ADaM", "reason": "Duplicate item already exists"}, {"item_code": "adsl", "item_type": "Dataset", "item_subtype": "ADaM", "reason": "Duplicate item already exists"}, {"item_code": "ae", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}, {"item_code": "cm", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}, {"item_code": "DM", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}, {"item_code": "lb", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}, {"item_code": "T_14_1_1_DEBUG", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_AFTER_RELOAD_1755121385", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_API_CHECK_003", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_API_TEST_1755121286", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_CHECK_001", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_DEBUG_1755121327", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_DICT_RESPONSE_1755121577", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_DIRECT_TEST_88409.656", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_FIXED_1755121372", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_MINIMAL_1755121531", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_NO_AUDIT_1755121437", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_NO_WEBSOCKET_1755121419", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_SIMPLE_OBJECT_1755121502", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_SIMPLE_RESPONSE_1755121452", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_TEST_001", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_TEST_FINAL_001", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_TEST_FIXED", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_VERIFY_001", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_VERIFY_002", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_VERIFY_1755121764", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t11", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t14.1.1", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t14.2.1", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t20.1.1", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t99.9.9", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "vs", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}]}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 08:58:01.007567
55	reporting_effort_items	5	COPY_FROM_REPORTING_EFFORT	\N	{"copy_operation": {"source_reporting_effort_id": 2, "source_item_ids": null, "created_count": 0, "skipped_count": 35, "created_item_ids": [], "skipped_items": [{"item_code": "adae", "item_type": "Dataset", "item_subtype": "ADaM", "reason": "Duplicate item already exists"}, {"item_code": "adeff", "item_type": "Dataset", "item_subtype": "ADaM", "reason": "Duplicate item already exists"}, {"item_code": "adsl", "item_type": "Dataset", "item_subtype": "ADaM", "reason": "Duplicate item already exists"}, {"item_code": "ae", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}, {"item_code": "cm", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}, {"item_code": "DM", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}, {"item_code": "f9.1.1", "item_type": "TLF", "item_subtype": "Figure", "reason": "Duplicate item already exists"}, {"item_code": "l16.1.1", "item_type": "TLF", "item_subtype": "Listing", "reason": "Duplicate item already exists"}, {"item_code": "lb", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}, {"item_code": "T_14_1_1_DEBUG", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_AFTER_RELOAD_1755121385", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_API_CHECK_003", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_API_TEST_1755121286", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_CHECK_001", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_DEBUG_1755121327", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_DICT_RESPONSE_1755121577", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_DIRECT_TEST_88409.656", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_FIXED_1755121372", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_MINIMAL_1755121531", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_NO_AUDIT_1755121437", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_NO_WEBSOCKET_1755121419", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_SIMPLE_OBJECT_1755121502", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_SIMPLE_RESPONSE_1755121452", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_TEST_001", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_TEST_FINAL_001", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_TEST_FIXED", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_VERIFY_001", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_VERIFY_002", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_VERIFY_1755121764", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t11", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t14.1.1", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t14.2.1", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t20.1.1", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t99.9.9", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "vs", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}]}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 08:58:08.998679
56	reporting_effort_items	211	DELETE	\N	{"deleted": {"id": 211, "reporting_effort_id": 5, "source_type": "reporting_effort", "source_id": 2, "source_item_id": 68, "item_type": "TLF", "item_subtype": "Figure", "item_code": "f9.1.1", "is_active": true, "created_at": "2025-08-14T08:58:00.927596", "updated_at": "2025-08-14T08:58:00.927596"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 08:58:49.735061
57	reporting_effort_items	212	DELETE	\N	{"deleted": {"id": 212, "reporting_effort_id": 5, "source_type": "reporting_effort", "source_id": 2, "source_item_id": 58, "item_type": "TLF", "item_subtype": "Listing", "item_code": "l16.1.1", "is_active": true, "created_at": "2025-08-14T08:58:00.948215", "updated_at": "2025-08-14T08:58:00.948215"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 08:58:52.873011
58	reporting_effort_items	5	COPY_FROM_REPORTING_EFFORT	\N	{"copy_operation": {"source_reporting_effort_id": 2, "source_item_ids": null, "created_count": 2, "skipped_count": 33, "created_item_ids": [213, 214], "skipped_items": [{"item_code": "adae", "item_type": "Dataset", "item_subtype": "ADaM", "reason": "Duplicate item already exists"}, {"item_code": "adeff", "item_type": "Dataset", "item_subtype": "ADaM", "reason": "Duplicate item already exists"}, {"item_code": "adsl", "item_type": "Dataset", "item_subtype": "ADaM", "reason": "Duplicate item already exists"}, {"item_code": "ae", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}, {"item_code": "cm", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}, {"item_code": "DM", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}, {"item_code": "lb", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}, {"item_code": "T_14_1_1_DEBUG", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_AFTER_RELOAD_1755121385", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_API_CHECK_003", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_API_TEST_1755121286", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_CHECK_001", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_DEBUG_1755121327", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_DICT_RESPONSE_1755121577", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_DIRECT_TEST_88409.656", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_FIXED_1755121372", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_MINIMAL_1755121531", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_NO_AUDIT_1755121437", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_NO_WEBSOCKET_1755121419", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_SIMPLE_OBJECT_1755121502", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_SIMPLE_RESPONSE_1755121452", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_TEST_001", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_TEST_FINAL_001", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_TEST_FIXED", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_VERIFY_001", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_VERIFY_002", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_VERIFY_1755121764", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t11", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t14.1.1", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t14.2.1", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t20.1.1", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t99.9.9", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "vs", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}]}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 08:59:01.424748
59	reporting_effort_items	5	COPY_FROM_REPORTING_EFFORT	\N	{"copy_operation": {"source_reporting_effort_id": 2, "source_item_ids": null, "created_count": 0, "skipped_count": 35, "created_item_ids": [], "skipped_items": [{"item_code": "adae", "item_type": "Dataset", "item_subtype": "ADaM", "reason": "Duplicate item already exists"}, {"item_code": "adeff", "item_type": "Dataset", "item_subtype": "ADaM", "reason": "Duplicate item already exists"}, {"item_code": "adsl", "item_type": "Dataset", "item_subtype": "ADaM", "reason": "Duplicate item already exists"}, {"item_code": "ae", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}, {"item_code": "cm", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}, {"item_code": "DM", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}, {"item_code": "f9.1.1", "item_type": "TLF", "item_subtype": "Figure", "reason": "Duplicate item already exists"}, {"item_code": "l16.1.1", "item_type": "TLF", "item_subtype": "Listing", "reason": "Duplicate item already exists"}, {"item_code": "lb", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}, {"item_code": "T_14_1_1_DEBUG", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_AFTER_RELOAD_1755121385", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_API_CHECK_003", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_API_TEST_1755121286", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_CHECK_001", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_DEBUG_1755121327", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_DICT_RESPONSE_1755121577", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_DIRECT_TEST_88409.656", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_FIXED_1755121372", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_MINIMAL_1755121531", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_NO_AUDIT_1755121437", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_NO_WEBSOCKET_1755121419", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_SIMPLE_OBJECT_1755121502", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_SIMPLE_RESPONSE_1755121452", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_TEST_001", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_TEST_FINAL_001", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_TEST_FIXED", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_VERIFY_001", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_VERIFY_002", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "T_VERIFY_1755121764", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t11", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t14.1.1", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t14.2.1", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t20.1.1", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "t99.9.9", "item_type": "TLF", "item_subtype": "Table", "reason": "Duplicate item already exists"}, {"item_code": "vs", "item_type": "Dataset", "item_subtype": "SDTM", "reason": "Duplicate item already exists"}]}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 13:02:16.703277
60	reporting_effort_items	68	DELETE	\N	{"deleted": {"id": 68, "reporting_effort_id": 2, "source_type": "package", "source_id": 1, "source_item_id": 34, "item_type": "TLF", "item_subtype": "Figure", "item_code": "f9.1.1", "is_active": true, "created_at": "2025-08-14T07:14:31.325015", "updated_at": "2025-08-14T07:14:31.325015"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 15:06:52.608861
61	reporting_effort_items	58	DELETE	\N	{"deleted": {"id": 58, "reporting_effort_id": 2, "source_type": "package", "source_id": 1, "source_item_id": 10, "item_type": "TLF", "item_subtype": "Listing", "item_code": "l16.1.1", "is_active": true, "created_at": "2025-08-14T07:14:31.194024", "updated_at": "2025-08-14T07:14:31.194024"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 15:06:55.375175
62	reporting_effort_items	1	DELETE	\N	{"deleted": {"id": 1, "reporting_effort_id": 2, "source_type": null, "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_14_1_1_DEBUG", "is_active": true, "created_at": "2025-08-13T20:36:10.502103", "updated_at": "2025-08-13T20:36:10.502103"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 15:07:10.77439
63	reporting_effort_items	2	COPY_TLF_FROM_PACKAGE	\N	{"copy_operation": {"source_package_id": 1, "source_item_ids": null, "item_type": "TLF", "summary": {"total_attempted": 7, "created_count": 2, "skipped_count": 5, "success": true}, "created_item_ids": [215, 216], "skipped_items": [{"item_type": "TLF", "item_subtype": "Table", "item_code": "t14.1.1", "reason": "already_exists"}, {"item_type": "TLF", "item_subtype": "Table", "item_code": "t14.2.1", "reason": "already_exists"}, {"item_type": "TLF", "item_subtype": "Table", "item_code": "t11", "reason": "already_exists"}, {"item_type": "TLF", "item_subtype": "Table", "item_code": "t20.1.1", "reason": "already_exists"}, {"item_type": "TLF", "item_subtype": "Table", "item_code": "t99.9.9", "reason": "already_exists"}]}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 15:07:17.76544
64	reporting_effort_items	59	DELETE	\N	{"deleted": {"id": 59, "reporting_effort_id": 2, "source_type": "package", "source_id": 1, "source_item_id": 14, "item_type": "Dataset", "item_subtype": "SDTM", "item_code": "DM", "is_active": true, "created_at": "2025-08-14T07:14:31.209681", "updated_at": "2025-08-14T07:14:31.209681"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 15:07:27.35938
65	reporting_effort_items	60	DELETE	\N	{"deleted": {"id": 60, "reporting_effort_id": 2, "source_type": "package", "source_id": 1, "source_item_id": 16, "item_type": "Dataset", "item_subtype": "SDTM", "item_code": "ae", "is_active": true, "created_at": "2025-08-14T07:14:31.231530", "updated_at": "2025-08-14T07:14:31.231530"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 15:07:36.762723
66	reporting_effort_items	2	COPY_DATASET_FROM_PACKAGE	\N	{"copy_operation": {"source_package_id": 1, "source_item_ids": null, "item_type": "Dataset", "summary": {"total_attempted": 8, "created_count": 2, "skipped_count": 6, "success": true}, "created_item_ids": [217, 218], "skipped_items": [{"item_type": "Dataset", "item_subtype": "SDTM", "item_code": "vs", "reason": "already_exists"}, {"item_type": "Dataset", "item_subtype": "SDTM", "item_code": "lb", "reason": "already_exists"}, {"item_type": "Dataset", "item_subtype": "ADaM", "item_code": "adsl", "reason": "already_exists"}, {"item_type": "Dataset", "item_subtype": "ADaM", "item_code": "adae", "reason": "already_exists"}, {"item_type": "Dataset", "item_subtype": "SDTM", "item_code": "cm", "reason": "already_exists"}, {"item_type": "Dataset", "item_subtype": "ADaM", "item_code": "adeff", "reason": "already_exists"}]}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 15:07:41.970866
67	reporting_effort_item_tracker	214	UPDATE	\N	{"before": {"id": 214, "reporting_effort_item_id": 216, "production_programmer_id": null, "qc_programmer_id": null, "production_status": "not_started", "qc_status": "not_started", "due_date": null, "qc_completion_date": null, "priority": "medium", "qc_level": null, "in_production_flag": false, "created_at": "2025-08-14T15:07:17.744784", "updated_at": "2025-08-14T15:07:17.744784"}, "after": {"id": 214, "reporting_effort_item_id": 216, "production_programmer_id": 2, "qc_programmer_id": 13, "production_status": "not_started", "qc_status": "not_started", "due_date": "2025-08-14", "qc_completion_date": "2025-08-14", "priority": "medium", "qc_level": null, "in_production_flag": false, "created_at": "2025-08-14T15:07:17.744784", "updated_at": "2025-08-14T21:32:44.222487"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 21:32:44.239563
68	reporting_effort_item_tracker	214	UPDATE	\N	{"before": {"id": 214, "reporting_effort_item_id": 216, "production_programmer_id": 2, "qc_programmer_id": 13, "production_status": "not_started", "qc_status": "not_started", "due_date": "2025-08-14", "qc_completion_date": "2025-08-14", "priority": "medium", "qc_level": null, "in_production_flag": false, "created_at": "2025-08-14T15:07:17.744784", "updated_at": "2025-08-14T21:32:44.222487"}, "after": {"id": 214, "reporting_effort_item_id": 216, "production_programmer_id": 2, "qc_programmer_id": 13, "production_status": "in_progress", "qc_status": "in_progress", "due_date": "2025-08-14", "qc_completion_date": "2025-08-14", "priority": "medium", "qc_level": null, "in_production_flag": false, "created_at": "2025-08-14T15:07:17.744784", "updated_at": "2025-08-14T21:33:07.627841"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 21:33:07.638839
69	reporting_effort_item_tracker	214	UPDATE	\N	{"before": {"id": 214, "reporting_effort_item_id": 216, "production_programmer_id": 2, "qc_programmer_id": 13, "production_status": "in_progress", "qc_status": "in_progress", "due_date": "2025-08-14", "qc_completion_date": "2025-08-14", "priority": "medium", "qc_level": null, "in_production_flag": false, "created_at": "2025-08-14T15:07:17.744784", "updated_at": "2025-08-14T21:33:07.627841"}, "after": {"id": 214, "reporting_effort_item_id": 216, "production_programmer_id": 2, "qc_programmer_id": 13, "production_status": "in_progress", "qc_status": "in_progress", "due_date": "2025-08-14", "qc_completion_date": "2025-08-14", "priority": "high", "qc_level": null, "in_production_flag": false, "created_at": "2025-08-14T15:07:17.744784", "updated_at": "2025-08-14T21:34:10.607571"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-14 21:34:10.610584
70	reporting_effort_item_tracker	213	UPDATE	\N	{"before": {"id": 213, "reporting_effort_item_id": 215, "production_programmer_id": null, "qc_programmer_id": null, "production_status": "not_started", "qc_status": "not_started", "due_date": null, "qc_completion_date": null, "priority": "medium", "qc_level": null, "in_production_flag": false, "created_at": "2025-08-14T15:07:17.724694", "updated_at": "2025-08-14T15:07:17.724694"}, "after": {"id": 213, "reporting_effort_item_id": 215, "production_programmer_id": 12, "qc_programmer_id": 12, "production_status": "not_started", "qc_status": "not_started", "due_date": "2025-08-15", "qc_completion_date": "2025-08-15", "priority": "medium", "qc_level": null, "in_production_flag": false, "created_at": "2025-08-14T15:07:17.724694", "updated_at": "2025-08-15T12:17:40.351305"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-15 12:17:40.367259
71	reporting_effort_item_tracker	214	UPDATE	\N	{"before": {"id": 214, "reporting_effort_item_id": 216, "production_programmer_id": 2, "qc_programmer_id": 13, "production_status": "in_progress", "qc_status": "in_progress", "due_date": "2025-08-14", "qc_completion_date": "2025-08-14", "priority": "high", "qc_level": null, "in_production_flag": false, "created_at": "2025-08-14T15:07:17.744784", "updated_at": "2025-08-14T21:34:10.607571"}, "after": {"id": 214, "reporting_effort_item_id": 216, "production_programmer_id": 2, "qc_programmer_id": 13, "production_status": "completed", "qc_status": "completed", "due_date": "2025-08-14", "qc_completion_date": "2025-08-14", "priority": "high", "qc_level": "3", "in_production_flag": false, "created_at": "2025-08-14T15:07:17.744784", "updated_at": "2025-08-15T15:09:44.043265"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-15 15:09:44.060512
72	reporting_effort_item_tracker	213	UPDATE	\N	{"before": {"id": 213, "reporting_effort_item_id": 215, "production_programmer_id": 12, "qc_programmer_id": 12, "production_status": "not_started", "qc_status": "not_started", "due_date": "2025-08-15", "qc_completion_date": "2025-08-15", "priority": "medium", "qc_level": null, "in_production_flag": false, "created_at": "2025-08-14T15:07:17.724694", "updated_at": "2025-08-15T12:17:40.351305"}, "after": {"id": 213, "reporting_effort_item_id": 215, "production_programmer_id": 12, "qc_programmer_id": 12, "production_status": "in_progress", "qc_status": "failed", "due_date": "2025-08-15", "qc_completion_date": "2025-08-15", "priority": "medium", "qc_level": "3", "in_production_flag": false, "created_at": "2025-08-14T15:07:17.724694", "updated_at": "2025-08-15T15:10:10.269503"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-15 15:10:10.289448
73	reporting_effort_item_tracker	75	UPDATE	\N	{"before": {"id": 75, "reporting_effort_item_id": 77, "production_programmer_id": null, "qc_programmer_id": null, "production_status": "not_started", "qc_status": "not_started", "due_date": null, "qc_completion_date": null, "priority": "medium", "qc_level": null, "in_production_flag": false, "created_at": "2025-08-14T08:37:28.520002", "updated_at": "2025-08-14T08:37:28.520002"}, "after": {"id": 75, "reporting_effort_item_id": 77, "production_programmer_id": null, "qc_programmer_id": null, "production_status": "not_started", "qc_status": "in_progress", "due_date": "2025-08-15", "qc_completion_date": "2025-08-15", "priority": "medium", "qc_level": "3", "in_production_flag": false, "created_at": "2025-08-14T08:37:28.520002", "updated_at": "2025-08-15T16:17:40.269025"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-15 16:17:40.277584
74	reporting_effort_tracker_comments	1	CREATE	13	{"created": {"id": 1, "tracker_id": 2, "user_id": 13, "parent_comment_id": null, "comment_text": "This is a test comment for tracker validation", "comment_type": "programmer_comment", "comment_category": "general", "is_pinned": false, "is_edited": false, "edited_at": null, "created_at": "2025-08-15T16:46:06.573881", "updated_at": null, "is_deleted": false}, "comment_type": "programmer_comment", "tracker_id": 2}	127.0.0.1	curl/7.87.0	2025-08-15 16:46:06.599686
75	reporting_effort_tracker_comments	2	CREATE	13	{"created": {"id": 2, "tracker_id": 2, "user_id": 13, "parent_comment_id": null, "comment_text": "Second test comment for verification", "comment_type": "biostat_comment", "comment_category": "general", "is_pinned": false, "is_edited": false, "edited_at": null, "created_at": "2025-08-15T16:49:25.416282", "updated_at": null, "is_deleted": false}, "comment_type": "biostat_comment", "tracker_id": 2}	127.0.0.1	curl/7.87.0	2025-08-15 16:49:25.427667
76	reporting_effort_tracker_comments	3	CREATE	13	{"created": {"id": 3, "tracker_id": 2, "user_id": 13, "parent_comment_id": null, "comment_text": "Testing WebSocket broadcasting", "comment_type": "biostat_comment", "comment_category": "general", "is_pinned": false, "is_edited": false, "edited_at": null, "created_at": "2025-08-15T16:50:32.882354", "updated_at": null, "is_deleted": false}, "comment_type": "biostat_comment", "tracker_id": 2}	127.0.0.1	curl/7.87.0	2025-08-15 16:50:32.901915
77	reporting_effort_tracker_comments	3	UPDATE	13	{"before": {"id": 3, "tracker_id": 2, "user_id": 13, "parent_comment_id": null, "comment_text": "Testing WebSocket broadcasting", "comment_type": "biostat_comment", "comment_category": "general", "is_pinned": false, "is_edited": false, "edited_at": null, "created_at": "2025-08-15T16:50:32.882354", "updated_at": null, "is_deleted": false}, "after": {"id": 3, "tracker_id": 2, "user_id": 13, "parent_comment_id": null, "comment_text": "Updated comment text for WebSocket testing", "comment_type": "biostat_comment", "comment_category": "general", "is_pinned": false, "is_edited": true, "edited_at": null, "created_at": "2025-08-15T16:50:32.882354", "updated_at": "2025-08-15T16:50:54.741390", "is_deleted": false}}	127.0.0.1	curl/7.87.0	2025-08-15 16:50:54.757292
78	reporting_effort_tracker_comments	3	SOFT_DELETE	13	{"deleted": {"id": 3, "tracker_id": 2, "user_id": 13, "parent_comment_id": null, "comment_text": "Updated comment text for WebSocket testing", "comment_type": "biostat_comment", "comment_category": "general", "is_pinned": false, "is_edited": true, "edited_at": null, "created_at": "2025-08-15T16:50:32.882354", "updated_at": "2025-08-15T16:50:54.741390", "is_deleted": false}, "deleted_by": 13}	127.0.0.1	curl/7.87.0	2025-08-15 16:50:59.125
79	reporting_effort_tracker_comments	4	CREATE	1	{"created": {"id": 4, "tracker_id": 214, "user_id": 1, "parent_comment_id": null, "comment_text": "test", "comment_type": "programmer_comment", "comment_category": "general", "is_pinned": false, "is_edited": false, "edited_at": null, "created_at": "2025-08-15T17:31:29.664849", "updated_at": null, "is_deleted": false}, "comment_type": "programmer_comment", "tracker_id": 214}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-15 17:31:29.673211
80	reporting_effort_tracker_comments	5	CREATE	1	{"created": {"id": 5, "tracker_id": 7, "user_id": 1, "parent_comment_id": null, "comment_text": "test", "comment_type": "biostat_comment", "comment_category": "general", "is_pinned": false, "is_edited": false, "edited_at": null, "created_at": "2025-08-15T17:32:20.791930", "updated_at": null, "is_deleted": false}, "comment_type": "biostat_comment", "tracker_id": 7}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-15 17:32:20.822799
81	reporting_effort_item_tracker	213	UPDATE	\N	{"before": {"id": 213, "reporting_effort_item_id": 215, "production_programmer_id": 12, "qc_programmer_id": 12, "production_status": "in_progress", "qc_status": "failed", "due_date": "2025-08-15", "qc_completion_date": "2025-08-15", "priority": "medium", "qc_level": "3", "in_production_flag": false, "created_at": "2025-08-14T15:07:17.724694", "updated_at": "2025-08-15T15:10:10.269503"}, "after": {"id": 213, "reporting_effort_item_id": 215, "production_programmer_id": 12, "qc_programmer_id": 12, "production_status": "on_hold", "qc_status": "not_started", "due_date": "2025-08-15", "qc_completion_date": "2025-08-15", "priority": "medium", "qc_level": "3", "in_production_flag": false, "created_at": "2025-08-14T15:07:17.724694", "updated_at": "2025-08-15T17:33:08.888974"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-15 17:33:08.905752
82	reporting_effort_item_tracker	7	UPDATE	\N	{"before": {"id": 7, "reporting_effort_item_id": 7, "production_programmer_id": null, "qc_programmer_id": null, "production_status": "not_started", "qc_status": "not_started", "due_date": null, "qc_completion_date": null, "priority": "medium", "qc_level": null, "in_production_flag": false, "created_at": "2025-08-13T21:26:20.762301", "updated_at": "2025-08-13T21:26:20.762301"}, "after": {"id": 7, "reporting_effort_item_id": 7, "production_programmer_id": null, "qc_programmer_id": null, "production_status": "not_started", "qc_status": "not_started", "due_date": "2025-08-15", "qc_completion_date": "2025-08-15", "priority": "high", "qc_level": "3", "in_production_flag": false, "created_at": "2025-08-13T21:26:20.762301", "updated_at": "2025-08-15T17:33:48.290060"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-15 17:33:48.30783
83	reporting_effort_item_tracker	28	UPDATE	\N	{"before": {"id": 28, "reporting_effort_item_id": 29, "production_programmer_id": null, "qc_programmer_id": null, "production_status": "not_started", "qc_status": "not_started", "due_date": null, "qc_completion_date": null, "priority": "medium", "qc_level": null, "in_production_flag": false, "created_at": "2025-08-13T21:43:05.865124", "updated_at": "2025-08-13T21:43:05.865124"}, "after": {"id": 28, "reporting_effort_item_id": 29, "production_programmer_id": 12, "qc_programmer_id": 9, "production_status": "in_progress", "qc_status": "in_progress", "due_date": "2025-08-15", "qc_completion_date": "2025-08-15", "priority": "high", "qc_level": "3", "in_production_flag": false, "created_at": "2025-08-13T21:43:05.865124", "updated_at": "2025-08-16T02:18:18.524339"}}	127.0.0.1	httr2/1.2.1 r-curl/6.4.0 libcurl/8.14.1	2025-08-16 02:18:18.541307
84	reporting_effort_items	219	CREATE	\N	{"created": {"id": 219, "reporting_effort_id": 18, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_14_1_1", "is_active": true, "created_at": "2025-08-18T05:07:12.698816", "updated_at": "2025-08-18T05:07:12.698816"}}	127.0.0.1	curl/7.87.0	2025-08-18 05:07:12.70739
85	reporting_effort_items	220	CREATE	\N	{"created": {"id": 220, "reporting_effort_id": 18, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "Dataset", "item_subtype": "ADaM", "item_code": "ADSL", "is_active": true, "created_at": "2025-08-18T05:07:12.820180", "updated_at": "2025-08-18T05:07:12.820180"}}	127.0.0.1	curl/7.87.0	2025-08-18 05:07:12.835737
86	reporting_effort_items	219	DELETE	\N	{"deleted": {"id": 219, "reporting_effort_id": 18, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_14_1_1", "is_active": true, "created_at": "2025-08-18T05:07:12.698816", "updated_at": "2025-08-18T05:07:12.698816"}}	127.0.0.1	curl/7.87.0	2025-08-18 05:07:13.595688
87	reporting_effort_items	221	CREATE	\N	{"created": {"id": 221, "reporting_effort_id": 18, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_2", "is_active": true, "created_at": "2025-08-18T05:07:13.696810", "updated_at": "2025-08-18T05:07:13.696810"}}	127.0.0.1	curl/7.87.0	2025-08-18 05:07:13.702832
88	reporting_effort_items	222	CREATE	\N	{"created": {"id": 222, "reporting_effort_id": 18, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_3", "is_active": true, "created_at": "2025-08-18T05:07:13.761925", "updated_at": "2025-08-18T05:07:13.761925"}}	127.0.0.1	curl/7.87.0	2025-08-18 05:07:13.767256
89	reporting_effort_items	223	CREATE	\N	{"created": {"id": 223, "reporting_effort_id": 18, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_4", "is_active": true, "created_at": "2025-08-18T05:07:13.838725", "updated_at": "2025-08-18T05:07:13.838725"}}	127.0.0.1	curl/7.87.0	2025-08-18 05:07:13.842693
90	reporting_effort_items	224	CREATE	\N	{"created": {"id": 224, "reporting_effort_id": 18, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_5", "is_active": true, "created_at": "2025-08-18T05:07:13.913469", "updated_at": "2025-08-18T05:07:13.913469"}}	127.0.0.1	curl/7.87.0	2025-08-18 05:07:13.916474
91	reporting_effort_items	220	DELETE	\N	{"deleted": {"id": 220, "reporting_effort_id": 18, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "Dataset", "item_subtype": "ADaM", "item_code": "ADSL", "is_active": true, "created_at": "2025-08-18T05:07:12.820180", "updated_at": "2025-08-18T05:07:12.820180"}}	127.0.0.1	curl/7.87.0	2025-08-18 05:07:14.450625
92	reporting_effort_items	225	CREATE	\N	{"created": {"id": 225, "reporting_effort_id": 19, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_14_1_1", "is_active": true, "created_at": "2025-08-18T07:21:15.706693", "updated_at": "2025-08-18T07:21:15.706693"}}	127.0.0.1	curl/7.87.0	2025-08-18 07:21:15.71705
93	reporting_effort_items	226	CREATE	\N	{"created": {"id": 226, "reporting_effort_id": 19, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "Dataset", "item_subtype": "ADaM", "item_code": "ADSL", "is_active": true, "created_at": "2025-08-18T07:21:15.867407", "updated_at": "2025-08-18T07:21:15.867407"}}	127.0.0.1	curl/7.87.0	2025-08-18 07:21:15.872667
94	reporting_effort_items	225	DELETE	\N	{"deleted": {"id": 225, "reporting_effort_id": 19, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_14_1_1", "is_active": true, "created_at": "2025-08-18T07:21:15.706693", "updated_at": "2025-08-18T07:21:15.706693"}}	127.0.0.1	curl/7.87.0	2025-08-18 07:21:16.913559
95	reporting_effort_items	227	CREATE	\N	{"created": {"id": 227, "reporting_effort_id": 19, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_2", "is_active": true, "created_at": "2025-08-18T07:21:17.042456", "updated_at": "2025-08-18T07:21:17.042456"}}	127.0.0.1	curl/7.87.0	2025-08-18 07:21:17.046858
96	reporting_effort_items	228	CREATE	\N	{"created": {"id": 228, "reporting_effort_id": 19, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_3", "is_active": true, "created_at": "2025-08-18T07:21:17.133431", "updated_at": "2025-08-18T07:21:17.133431"}}	127.0.0.1	curl/7.87.0	2025-08-18 07:21:17.139451
97	reporting_effort_items	229	CREATE	\N	{"created": {"id": 229, "reporting_effort_id": 19, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_4", "is_active": true, "created_at": "2025-08-18T07:21:17.213089", "updated_at": "2025-08-18T07:21:17.213600"}}	127.0.0.1	curl/7.87.0	2025-08-18 07:21:17.219106
98	reporting_effort_items	230	CREATE	\N	{"created": {"id": 230, "reporting_effort_id": 19, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Figure", "item_code": "F_14_1_5", "is_active": true, "created_at": "2025-08-18T07:21:17.309414", "updated_at": "2025-08-18T07:21:17.309414"}}	127.0.0.1	curl/7.87.0	2025-08-18 07:21:17.316771
99	reporting_effort_items	226	DELETE	\N	{"deleted": {"id": 226, "reporting_effort_id": 19, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "Dataset", "item_subtype": "ADaM", "item_code": "ADSL", "is_active": true, "created_at": "2025-08-18T07:21:15.867407", "updated_at": "2025-08-18T07:21:15.867407"}}	127.0.0.1	curl/7.87.0	2025-08-18 07:21:17.995857
100	reporting_effort_items	242	CREATE	\N	{"created": {"id": 242, "reporting_effort_id": 24, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_DELETE_TEST", "is_active": true, "created_at": "2025-08-18T18:40:13.991857", "updated_at": "2025-08-18T18:40:13.991857"}}	127.0.0.1	curl/7.87.0	2025-08-18 18:40:14.005297
101	reporting_effort_items	243	CREATE	\N	{"created": {"id": 243, "reporting_effort_id": 24, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "Dataset", "item_subtype": "ADaM", "item_code": "ADSL_DELETE_TEST", "is_active": true, "created_at": "2025-08-18T18:40:14.276307", "updated_at": "2025-08-18T18:40:14.276307"}}	127.0.0.1	curl/7.87.0	2025-08-18 18:40:14.287509
102	reporting_effort_items	242	DELETE	\N	{"deleted": {"id": 242, "reporting_effort_id": 24, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_DELETE_TEST", "is_active": true, "created_at": "2025-08-18T18:40:13.991857", "updated_at": "2025-08-18T18:40:13.991857"}}	127.0.0.1	curl/7.87.0	2025-08-18 18:40:15.992437
103	reporting_effort_items	243	DELETE	\N	{"deleted": {"id": 243, "reporting_effort_id": 24, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "Dataset", "item_subtype": "ADaM", "item_code": "ADSL_DELETE_TEST", "is_active": true, "created_at": "2025-08-18T18:40:14.276307", "updated_at": "2025-08-18T18:40:14.276307"}}	127.0.0.1	curl/7.87.0	2025-08-18 18:40:16.055568
104	reporting_effort_item_tracker	3	DELETE	\N	{"deleted": {"id": 3, "reporting_effort_item_id": 3, "production_programmer_id": null, "qc_programmer_id": null, "production_status": "not_started", "qc_status": "not_started", "due_date": null, "qc_completion_date": null, "priority": "medium", "qc_level": null, "in_production_flag": false, "unresolved_comment_count": 0, "created_at": "2025-08-13T21:07:56.183836", "updated_at": "2025-08-13T21:07:56.183836"}}	127.0.0.1	curl/7.87.0	2025-08-18 18:40:37.949282
105	reporting_effort_items	244	CREATE	\N	{"created": {"id": 244, "reporting_effort_id": 25, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_DELETE_TEST", "is_active": true, "created_at": "2025-08-18T18:41:12.598463", "updated_at": "2025-08-18T18:41:12.598463"}}	127.0.0.1	curl/7.87.0	2025-08-18 18:41:12.607788
106	reporting_effort_items	245	CREATE	\N	{"created": {"id": 245, "reporting_effort_id": 25, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "Dataset", "item_subtype": "ADaM", "item_code": "ADSL_DELETE_TEST", "is_active": true, "created_at": "2025-08-18T18:41:12.881214", "updated_at": "2025-08-18T18:41:12.881214"}}	127.0.0.1	curl/7.87.0	2025-08-18 18:41:12.899446
107	reporting_effort_items	244	DELETE	\N	{"deleted": {"id": 244, "reporting_effort_id": 25, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "TLF", "item_subtype": "Table", "item_code": "T_DELETE_TEST", "is_active": true, "created_at": "2025-08-18T18:41:12.598463", "updated_at": "2025-08-18T18:41:12.598463"}}	127.0.0.1	curl/7.87.0	2025-08-18 18:41:14.569617
108	reporting_effort_items	245	DELETE	\N	{"deleted": {"id": 245, "reporting_effort_id": 25, "source_type": "custom", "source_id": null, "source_item_id": null, "item_type": "Dataset", "item_subtype": "ADaM", "item_code": "ADSL_DELETE_TEST", "is_active": true, "created_at": "2025-08-18T18:41:12.881214", "updated_at": "2025-08-18T18:41:12.881214"}}	127.0.0.1	curl/7.87.0	2025-08-18 18:41:14.635407
109	reporting_effort_item_tracker	4	DELETE	\N	{"deleted": {"id": 4, "reporting_effort_item_id": 4, "production_programmer_id": null, "qc_programmer_id": null, "production_status": "not_started", "qc_status": "not_started", "due_date": null, "qc_completion_date": null, "priority": "medium", "qc_level": null, "in_production_flag": false, "unresolved_comment_count": 0, "created_at": "2025-08-13T21:10:15.966710", "updated_at": "2025-08-13T21:10:15.966710"}}	127.0.0.1	curl/7.87.0	2025-08-18 18:42:17.629475
110	reporting_effort_item_tracker	5	DELETE	\N	{"deleted": {"id": 5, "reporting_effort_item_id": 5, "production_programmer_id": null, "qc_programmer_id": null, "production_status": "not_started", "qc_status": "not_started", "due_date": null, "qc_completion_date": null, "priority": "medium", "qc_level": null, "in_production_flag": false, "unresolved_comment_count": 0, "created_at": "2025-08-13T21:11:25.854159", "updated_at": "2025-08-13T21:11:25.854159"}}	127.0.0.1	curl/7.87.0	2025-08-18 18:42:54.855476
111	reporting_effort_item_tracker	7	DELETE	\N	{"deleted": {"id": 7, "reporting_effort_item_id": 7, "production_programmer_id": null, "qc_programmer_id": null, "production_status": "not_started", "qc_status": "not_started", "due_date": "2025-08-15", "qc_completion_date": "2025-08-15", "priority": "high", "qc_level": "3", "in_production_flag": false, "unresolved_comment_count": 2, "created_at": "2025-08-13T21:26:20.762301", "updated_at": "2025-08-18T17:26:29.372677"}}	127.0.0.1	curl/7.87.0	2025-08-18 18:45:11.389897
112	reporting_effort_item_tracker	8	DELETE	\N	{"deleted": {"id": 8, "reporting_effort_item_id": 8, "production_programmer_id": null, "qc_programmer_id": null, "production_status": "not_started", "qc_status": "not_started", "due_date": null, "qc_completion_date": null, "priority": "medium", "qc_level": null, "in_production_flag": false, "unresolved_comment_count": 0, "created_at": "2025-08-13T21:36:36.018635", "updated_at": "2025-08-13T21:36:36.018635"}}	127.0.0.1	curl/7.87.0	2025-08-18 18:45:34.979044
\.


--
-- Data for Name: database_releases; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.database_releases (id, study_id, database_release_label, created_at, updated_at) FROM stdin;
1	3	test_db	2025-08-09 17:30:43.204675	2025-08-09 17:30:43.204675
2	7	103_db	2025-08-10 22:45:18.708679	2025-08-10 22:45:18.708679
3	8	db104s	2025-08-10 22:50:44.622896	2025-08-10 22:55:08.129773
4	8	db104_2	2025-08-10 23:04:17.609147	2025-08-10 23:04:30.232292
5	2	Release 1.0	2025-08-11 13:02:35.911702	2025-08-11 13:02:35.911702
6	2	releases	2025-08-11 13:11:46.767055	2025-08-11 13:11:46.767055
8	2	test_release	2025-08-11 15:38:02.442943	2025-08-11 15:38:02.442943
10	2	test  release	2025-08-11 15:38:22.312071	2025-08-11 15:38:22.312071
9	2	Test_Release_Updated_Via_Script	2025-08-11 15:38:11.976006	2025-08-11 20:46:46.438371
11	2	releases 2.0	2025-08-11 15:54:06.824202	2025-08-11 21:14:43.549941
20	19	Debug DB Release	2025-08-13 21:38:46.801902	2025-08-13 21:38:46.801902
24	25	Test DB Release	2025-08-18 05:06:22.957791	2025-08-18 05:06:22.957791
27	32	January 2025 Primary Analysis	2025-08-18 07:23:01.355706	2025-08-18 07:23:01.355706
28	33	January 2025 Primary Analysis	2025-08-18 07:24:13.292934	2025-08-18 07:24:13.292934
29	34	January 2025 Primary Analysis	2025-08-18 07:24:28.346068	2025-08-18 07:24:28.346068
30	35	January 2025 Primary Analysis	2025-08-18 07:24:53.354144	2025-08-18 07:24:53.354144
\.


--
-- Data for Name: package_dataset_details; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.package_dataset_details (id, package_item_id, label, sorting_order, acronyms) FROM stdin;
1	14	Demographics	1	\N
3	16	Adverse Events	2	\N
5	18	Vital Signs	4	\N
6	19	Laboratory Tests	5	\N
7	20	Subject-Level Analysis Dataset	6	\N
8	21	Adverse Events Analysis Dataset	7	\N
10	32	Concomitant Medications	3	\N
11	33	Efficacy Analysis Dataset	8	\N
\.


--
-- Data for Name: package_item_acronyms; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.package_item_acronyms (package_item_id, acronym_id) FROM stdin;
9	14
9	15
\.


--
-- Data for Name: package_item_footnotes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.package_item_footnotes (package_item_id, footnote_id, sequence_number) FROM stdin;
8	6	1
8	7	2
9	12	1
9	13	2
10	19	1
\.


--
-- Data for Name: package_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.package_items (id, package_id, item_type, item_subtype, item_code, created_at, updated_at) FROM stdin;
8	1	TLF	Table	t14.1.1	2025-08-12 03:25:36.783725	2025-08-12 03:25:36.783725
9	1	TLF	Table	t14.2.1	2025-08-12 03:27:13.822017	2025-08-12 03:27:13.822017
10	1	TLF	Listing	l16.1.1	2025-08-12 03:27:13.864473	2025-08-12 03:27:13.864473
14	1	Dataset	SDTM	DM	2025-08-12 05:14:12.354653	2025-08-12 05:14:12.354653
16	1	Dataset	SDTM	ae	2025-08-12 06:07:54.807715	2025-08-12 06:07:54.807715
18	1	Dataset	SDTM	vs	2025-08-12 06:07:54.857062	2025-08-12 06:07:54.857062
19	1	Dataset	SDTM	lb	2025-08-12 06:07:54.881631	2025-08-12 06:07:54.881631
20	1	Dataset	ADaM	adsl	2025-08-12 06:07:54.908069	2025-08-12 06:07:54.908069
21	1	Dataset	ADaM	adae	2025-08-12 06:07:54.934904	2025-08-12 06:07:54.934904
29	1	TLF	Table	t11	2025-08-12 06:47:40.612349	2025-08-12 06:47:40.612349
32	1	Dataset	SDTM	cm	2025-08-12 06:50:33.502519	2025-08-12 06:50:33.502519
33	1	Dataset	ADaM	adeff	2025-08-12 06:50:33.621739	2025-08-12 06:50:33.621739
34	1	TLF	Figure	f9.1.1	2025-08-12 07:10:26.667254	2025-08-12 07:10:26.667254
35	1	TLF	Table	t20.1.1	2025-08-12 07:10:26.726404	2025-08-12 07:10:26.726404
36	1	TLF	Table	t99.9.9	2025-08-12 07:50:32.130579	2025-08-12 07:50:32.130579
\.


--
-- Data for Name: package_tlf_details; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.package_tlf_details (id, package_item_id, title_id, population_flag_id, ich_category_id) FROM stdin;
5	8	4	8	5
6	9	9	10	11
7	10	16	17	18
14	29	4	8	5
17	34	42	8	\N
18	35	22	8	11
19	36	43	\N	\N
\.


--
-- Data for Name: packages; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.packages (id, package_name, created_at, updated_at) FROM stdin;
1	Standard	2025-08-09 06:33:15.089183	2025-08-09 06:33:15.089183
3	Test Package	2025-08-12 03:30:50.369778	2025-08-12 03:30:50.369778
4	Test Package 2	2025-08-12 03:30:50.701506	2025-08-12 03:30:50.701506
5	DMC	2025-08-12 05:00:19.355917	2025-08-12 05:00:19.355917
2	tests	2025-08-09 06:49:44.562933	2025-08-12 05:08:44.692411
6	Clinical Trial Package A	2025-08-12 05:09:11.112163	2025-08-12 05:09:11.112163
7	Safety Analysis Package	2025-08-12 05:09:11.170087	2025-08-12 05:09:11.170087
8	Efficacy Report Package	2025-08-12 05:09:11.189679	2025-08-12 05:09:11.189679
9	Regulatory Submission Package	2025-08-12 05:09:11.204215	2025-08-12 05:09:11.204215
\.


--
-- Data for Name: reporting_effort_dataset_details; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_effort_dataset_details (id, reporting_effort_item_id, label, sorting_order, acronyms) FROM stdin;
3	61	Vital Signs	4	\N
4	62	Laboratory Tests	5	\N
5	63	Subject-Level Analysis Dataset	6	\N
6	64	Adverse Events Analysis Dataset	7	\N
7	66	Concomitant Medications	3	\N
8	67	Efficacy Analysis Dataset	8	\N
9	71	Adverse Events Analysis Dataset	7	\N
10	72	Efficacy Analysis Dataset	8	\N
11	73	Subject-Level Analysis Dataset	6	\N
12	74	Adverse Events	2	\N
13	75	Concomitant Medications	3	\N
14	76	Demographics	1	\N
15	79	Laboratory Tests	5	\N
16	105	Vital Signs	4	\N
25	141	Adverse Events Analysis Dataset	7	\N
26	142	Efficacy Analysis Dataset	8	\N
27	143	Subject-Level Analysis Dataset	6	\N
28	144	Adverse Events	2	\N
29	145	Concomitant Medications	3	\N
30	146	Demographics	1	\N
31	149	Laboratory Tests	5	\N
32	175	Vital Signs	4	\N
33	176	Adverse Events Analysis Dataset	7	\N
34	177	Efficacy Analysis Dataset	8	\N
35	178	Subject-Level Analysis Dataset	6	\N
36	179	Adverse Events	2	\N
37	180	Concomitant Medications	3	\N
38	181	Demographics	1	\N
39	184	Laboratory Tests	5	\N
40	210	Vital Signs	4	\N
41	217	Demographics	1	\N
42	218	Adverse Events	2	\N
\.


--
-- Data for Name: reporting_effort_item_acronyms; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_effort_item_acronyms (reporting_effort_item_id, acronym_id) FROM stdin;
57	14
57	15
102	14
102	15
172	14
172	15
207	14
207	15
\.


--
-- Data for Name: reporting_effort_item_footnotes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_effort_item_footnotes (reporting_effort_item_id, footnote_id, sequence_number) FROM stdin;
56	6	1
56	7	2
57	12	1
57	13	2
78	19	1
101	6	1
101	7	2
102	12	1
102	13	2
148	19	1
171	6	1
171	7	2
172	12	1
172	13	2
206	6	1
206	7	2
207	12	1
207	13	2
214	19	1
215	19	1
\.


--
-- Data for Name: reporting_effort_item_tracker; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_effort_item_tracker (id, reporting_effort_item_id, production_programmer_id, production_status, due_date, priority, qc_level, qc_programmer_id, qc_status, qc_completion_date, in_production_flag, created_at, updated_at, unresolved_comment_count) FROM stdin;
82	84	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.673507	2025-08-18 03:26:28.499815	1
62	64	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 07:14:31.279935	2025-08-18 01:50:08.562397	1
28	29	12	in_progress	2025-08-15	high	3	9	in_progress	2025-08-15	f	2025-08-13 21:43:05.865124	2025-08-17 20:32:51.710121	1
81	83	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.657713	2025-08-18 03:45:10.770695	2
21	21	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:38:56.166746	2025-08-13 21:38:56.166746	0
22	23	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:39:19.666478	2025-08-13 21:39:19.666478	0
23	24	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:40:09.280318	2025-08-13 21:40:09.280318	0
24	25	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:40:26.694174	2025-08-13 21:40:26.694174	0
26	27	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:42:07.239602	2025-08-13 21:42:07.239602	0
27	28	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:42:52.619689	2025-08-13 21:42:52.619689	0
29	30	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:43:39.859682	2025-08-13 21:43:39.859682	0
30	31	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:43:57.565414	2025-08-13 21:43:57.565414	0
31	32	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:44:12.612571	2025-08-13 21:44:12.612571	0
32	33	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:45:02.549642	2025-08-13 21:45:02.549642	0
33	34	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:45:31.947447	2025-08-13 21:45:31.947447	0
34	35	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:46:17.525731	2025-08-13 21:46:17.525731	0
41	42	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:49:24.749327	2025-08-13 21:49:24.749327	0
2	2	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:04:02.365308	2025-08-18 06:27:28.402827	6
76	78	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.543451	2025-08-18 15:39:52.562883	6
78	80	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.59812	2025-08-18 16:57:15.556476	2
75	77	\N	not_started	2025-08-15	medium	3	\N	in_progress	2025-08-15	f	2025-08-14 08:37:28.520002	2025-08-18 16:59:39.53369	1
54	56	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 07:14:31.139202	2025-08-14 07:14:31.139202	0
55	57	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 07:14:31.179269	2025-08-14 07:14:31.179269	0
25	26	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:41:26.980814	2025-08-18 18:21:30.05769	2
6	6	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:16:42.179738	2025-08-18 18:22:02.471378	3
59	61	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 07:14:31.243812	2025-08-14 07:14:31.243812	0
60	62	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 07:14:31.254942	2025-08-14 07:14:31.254942	0
61	63	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 07:14:31.268431	2025-08-14 07:14:31.268431	0
63	65	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 07:14:31.291952	2025-08-14 07:14:31.291952	0
64	66	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 07:14:31.304244	2025-08-14 07:14:31.304244	0
65	67	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 07:14:31.314107	2025-08-14 07:14:31.314107	0
67	69	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 07:14:31.3391	2025-08-14 07:14:31.3391	0
68	70	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 07:14:31.350068	2025-08-14 07:14:31.350068	0
69	71	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.392765	2025-08-14 08:37:28.392765	0
70	72	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.418897	2025-08-14 08:37:28.418897	0
71	73	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.426165	2025-08-14 08:37:28.426165	0
72	74	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.443905	2025-08-14 08:37:28.443905	0
73	75	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.46947	2025-08-14 08:37:28.46947	0
74	76	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.496724	2025-08-14 08:37:28.496724	0
77	79	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.574497	2025-08-14 08:37:28.574497	0
79	81	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.620635	2025-08-14 08:37:28.620635	0
80	82	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.642429	2025-08-14 08:37:28.642429	0
83	85	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.695266	2025-08-14 08:37:28.695266	0
84	86	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.70497	2025-08-14 08:37:28.70497	0
85	87	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.721387	2025-08-14 08:37:28.721387	0
86	88	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.736577	2025-08-14 08:37:28.736577	0
87	89	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.75222	2025-08-14 08:37:28.75222	0
88	90	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.767964	2025-08-14 08:37:28.767964	0
89	91	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.783965	2025-08-14 08:37:28.783965	0
90	92	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.799754	2025-08-14 08:37:28.799754	0
91	93	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.815569	2025-08-14 08:37:28.815569	0
92	94	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.822332	2025-08-14 08:37:28.822332	0
93	95	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.831455	2025-08-14 08:37:28.831455	0
94	96	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.847393	2025-08-14 08:37:28.847393	0
95	97	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.87247	2025-08-14 08:37:28.87247	0
96	98	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.87946	2025-08-14 08:37:28.87946	0
97	99	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.895399	2025-08-14 08:37:28.895399	0
98	100	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.911093	2025-08-14 08:37:28.911093	0
99	101	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.927076	2025-08-14 08:37:28.927076	0
100	102	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.942875	2025-08-14 08:37:28.942875	0
101	103	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.95861	2025-08-14 08:37:28.95861	0
102	104	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.974454	2025-08-14 08:37:28.974454	0
103	105	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:37:28.990208	2025-08-14 08:37:28.990208	0
216	218	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 15:07:41.951851	2025-08-18 01:52:14.476602	1
146	148	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.613492	2025-08-18 15:53:55.478469	1
148	150	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.651138	2025-08-18 16:15:27.948414	1
145	147	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.594169	2025-08-18 16:23:55.598353	9
139	141	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.478854	2025-08-14 08:43:40.478854	0
140	142	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.51247	2025-08-14 08:43:40.51247	0
141	143	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.530749	2025-08-14 08:43:40.530749	0
142	144	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.545223	2025-08-14 08:43:40.545223	0
143	145	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.563045	2025-08-14 08:43:40.563045	0
144	146	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.578126	2025-08-14 08:43:40.578126	0
147	149	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.631042	2025-08-14 08:43:40.631042	0
150	152	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.680389	2025-08-14 08:43:40.680389	0
151	153	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.695951	2025-08-14 08:43:40.695951	0
152	154	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.71413	2025-08-14 08:43:40.71413	0
153	155	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.726723	2025-08-14 08:43:40.726723	0
154	156	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.742451	2025-08-14 08:43:40.742451	0
155	157	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.758238	2025-08-14 08:43:40.758238	0
156	158	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.764617	2025-08-14 08:43:40.764617	0
157	159	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.77429	2025-08-14 08:43:40.77429	0
158	160	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.789948	2025-08-14 08:43:40.789948	0
159	161	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.814859	2025-08-14 08:43:40.814859	0
160	162	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.831277	2025-08-14 08:43:40.831277	0
161	163	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.837676	2025-08-14 08:43:40.837676	0
162	164	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.853425	2025-08-14 08:43:40.853425	0
163	165	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.86906	2025-08-14 08:43:40.86906	0
164	166	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.884746	2025-08-14 08:43:40.884746	0
165	167	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.900485	2025-08-14 08:43:40.900485	0
166	168	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.916252	2025-08-14 08:43:40.916252	0
167	169	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.932215	2025-08-14 08:43:40.932215	0
168	170	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.932215	2025-08-14 08:43:40.932215	0
169	171	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.96375	2025-08-14 08:43:40.96375	0
170	172	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.97986	2025-08-14 08:43:40.97986	0
171	173	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.99564	2025-08-14 08:43:40.99564	0
172	174	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:41.011344	2025-08-14 08:43:41.011344	0
173	175	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:41.031386	2025-08-14 08:43:41.031386	0
174	176	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.600462	2025-08-14 08:48:44.600462	0
175	177	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.628122	2025-08-14 08:48:44.628122	0
176	178	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.645759	2025-08-14 08:48:44.645759	0
177	179	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.661852	2025-08-14 08:48:44.661852	0
178	180	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.679445	2025-08-14 08:48:44.679445	0
179	181	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.694808	2025-08-14 08:48:44.694808	0
149	151	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:43:40.665395	2025-08-18 16:40:22.045558	2
182	184	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.745869	2025-08-14 08:48:44.745869	0
183	185	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.761968	2025-08-14 08:48:44.761968	0
184	186	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.78105	2025-08-14 08:48:44.78105	0
185	187	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.796584	2025-08-14 08:48:44.796584	0
186	188	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.810601	2025-08-14 08:48:44.810601	0
187	189	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.825209	2025-08-14 08:48:44.825209	0
188	190	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.839277	2025-08-14 08:48:44.839277	0
189	191	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.845366	2025-08-14 08:48:44.845366	0
190	192	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.860029	2025-08-14 08:48:44.860029	0
191	193	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.875895	2025-08-14 08:48:44.875895	0
192	194	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.895858	2025-08-14 08:48:44.895858	0
193	195	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.920041	2025-08-14 08:48:44.920041	0
194	196	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.935933	2025-08-14 08:48:44.935933	0
195	197	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.95235	2025-08-14 08:48:44.95235	0
196	198	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.963937	2025-08-14 08:48:44.963937	0
197	199	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.969946	2025-08-14 08:48:44.969946	0
198	200	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:44.996261	2025-08-14 08:48:44.996261	0
199	201	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:45.006907	2025-08-14 08:48:45.006907	0
200	202	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:45.018327	2025-08-14 08:48:45.018327	0
201	203	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:45.033551	2025-08-14 08:48:45.033551	0
202	204	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:45.049686	2025-08-14 08:48:45.049686	0
203	205	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:45.069	2025-08-14 08:48:45.069	0
204	206	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:45.087284	2025-08-14 08:48:45.087284	0
205	207	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:45.096704	2025-08-14 08:48:45.096704	0
206	208	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:45.128784	2025-08-14 08:48:45.128784	0
207	209	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:45.144801	2025-08-14 08:48:45.144801	0
208	210	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:48:45.160487	2025-08-14 08:48:45.160487	0
213	215	12	on_hold	2025-08-15	medium	3	12	not_started	2025-08-15	f	2025-08-14 15:07:17.724694	2025-08-18 16:53:40.311031	1
211	213	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:59:01.300328	2025-08-14 08:59:01.300328	0
212	214	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 08:59:01.373574	2025-08-14 08:59:01.373574	0
215	217	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-14 15:07:41.920408	2025-08-14 15:07:41.920408	0
214	216	2	completed	2025-08-14	high	3	13	completed	2025-08-14	f	2025-08-14 15:07:17.744784	2025-08-18 18:21:11.53076	2
\.


--
-- Data for Name: reporting_effort_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_effort_items (id, reporting_effort_id, source_type, source_id, source_item_id, item_type, item_subtype, item_code, is_active, created_at, updated_at) FROM stdin;
2	2	\N	\N	\N	TLF	Table	T_TEST_001	t	2025-08-13 21:04:02.355855	2025-08-13 21:04:02.355855
3	2	custom	\N	\N	TLF	Table	T_TEST_FINAL_001	t	2025-08-13 21:07:56.175366	2025-08-13 21:07:56.175366
4	2	custom	\N	\N	TLF	Table	T_VERIFY_001	t	2025-08-13 21:10:15.955501	2025-08-13 21:10:15.955501
5	2	\N	\N	\N	TLF	Table	T_VERIFY_002	t	2025-08-13 21:11:25.854159	2025-08-13 21:11:25.854159
6	2	custom	\N	\N	TLF	Table	T_CHECK_001	t	2025-08-13 21:16:42.148637	2025-08-13 21:16:42.148637
7	2	custom	\N	\N	TLF	Table	T_API_CHECK_003	t	2025-08-13 21:26:20.756582	2025-08-13 21:26:20.756582
8	2	custom	\N	\N	TLF	Table	T_TEST_FIXED	t	2025-08-13 21:36:36.005737	2025-08-13 21:36:36.005737
21	13	custom	\N	\N	TLF	Table	T_DEBUG_1	t	2025-08-13 21:38:56.166746	2025-08-13 21:38:56.166746
23	13	custom	\N	\N	TLF	Table	T_DEBUG_1755121159	t	2025-08-13 21:39:19.660966	2025-08-13 21:39:19.660966
24	13	custom	\N	\N	TLF	Table	T_DEBUG_UNIQUE_1755121209	t	2025-08-13 21:40:09.27834	2025-08-13 21:40:09.27834
25	2	custom	\N	\N	TLF	Table	T_DIRECT_TEST_88409.656	t	2025-08-13 21:40:26.678508	2025-08-13 21:40:26.678508
26	2	custom	\N	\N	TLF	Table	T_API_TEST_1755121286	t	2025-08-13 21:41:26.978578	2025-08-13 21:41:26.978578
27	2	custom	\N	\N	TLF	Table	T_DEBUG_1755121327	t	2025-08-13 21:42:07.223666	2025-08-13 21:42:07.223666
28	2	custom	\N	\N	TLF	Table	T_FIXED_1755121372	t	2025-08-13 21:42:52.603785	2025-08-13 21:42:52.603785
29	2	custom	\N	\N	TLF	Table	T_AFTER_RELOAD_1755121385	t	2025-08-13 21:43:05.862559	2025-08-13 21:43:05.862559
30	2	custom	\N	\N	TLF	Table	T_NO_WEBSOCKET_1755121419	t	2025-08-13 21:43:39.843596	2025-08-13 21:43:39.843596
31	2	custom	\N	\N	TLF	Table	T_NO_AUDIT_1755121437	t	2025-08-13 21:43:57.560409	2025-08-13 21:43:57.560409
32	2	custom	\N	\N	TLF	Table	T_SIMPLE_RESPONSE_1755121452	t	2025-08-13 21:44:12.588389	2025-08-13 21:44:12.588389
33	2	custom	\N	\N	TLF	Table	T_SIMPLE_OBJECT_1755121502	t	2025-08-13 21:45:02.533497	2025-08-13 21:45:02.533497
34	2	custom	\N	\N	TLF	Table	T_MINIMAL_1755121531	t	2025-08-13 21:45:31.919723	2025-08-13 21:45:31.919723
35	2	custom	\N	\N	TLF	Table	T_DICT_RESPONSE_1755121577	t	2025-08-13 21:46:17.5121	2025-08-13 21:46:17.5121
42	2	custom	\N	\N	TLF	Table	T_VERIFY_1755121764	t	2025-08-13 21:49:24.734302	2025-08-13 21:49:24.734302
56	2	package	1	8	TLF	Table	t14.1.1	t	2025-08-14 07:14:31.11925	2025-08-14 07:14:31.11925
57	2	package	1	9	TLF	Table	t14.2.1	t	2025-08-14 07:14:31.179269	2025-08-14 07:14:31.179269
61	2	package	1	18	Dataset	SDTM	vs	t	2025-08-14 07:14:31.242813	2025-08-14 07:14:31.242813
62	2	package	1	19	Dataset	SDTM	lb	t	2025-08-14 07:14:31.253936	2025-08-14 07:14:31.253936
63	2	package	1	20	Dataset	ADaM	adsl	t	2025-08-14 07:14:31.266431	2025-08-14 07:14:31.266431
64	2	package	1	21	Dataset	ADaM	adae	t	2025-08-14 07:14:31.27843	2025-08-14 07:14:31.27843
65	2	package	1	29	TLF	Table	t11	t	2025-08-14 07:14:31.290944	2025-08-14 07:14:31.290944
66	2	package	1	32	Dataset	SDTM	cm	t	2025-08-14 07:14:31.301865	2025-08-14 07:14:31.301865
67	2	package	1	33	Dataset	ADaM	adeff	t	2025-08-14 07:14:31.312839	2025-08-14 07:14:31.312839
69	2	package	1	35	TLF	Table	t20.1.1	t	2025-08-14 07:14:31.337732	2025-08-14 07:14:31.337732
70	2	package	1	36	TLF	Table	t99.9.9	t	2025-08-14 07:14:31.349067	2025-08-14 07:14:31.349067
71	4	reporting_effort	2	64	Dataset	ADaM	adae	t	2025-08-14 08:37:28.392765	2025-08-14 08:37:28.392765
72	4	reporting_effort	2	67	Dataset	ADaM	adeff	t	2025-08-14 08:37:28.411062	2025-08-14 08:37:28.411062
73	4	reporting_effort	2	63	Dataset	ADaM	adsl	t	2025-08-14 08:37:28.426165	2025-08-14 08:37:28.426165
74	4	reporting_effort	2	60	Dataset	SDTM	ae	t	2025-08-14 08:37:28.443905	2025-08-14 08:37:28.443905
75	4	reporting_effort	2	66	Dataset	SDTM	cm	t	2025-08-14 08:37:28.459281	2025-08-14 08:37:28.459281
76	4	reporting_effort	2	59	Dataset	SDTM	DM	t	2025-08-14 08:37:28.489983	2025-08-14 08:37:28.489983
77	4	reporting_effort	2	68	TLF	Figure	f9.1.1	t	2025-08-14 08:37:28.520002	2025-08-14 08:37:28.520002
78	4	reporting_effort	2	58	TLF	Listing	l16.1.1	t	2025-08-14 08:37:28.543451	2025-08-14 08:37:28.543451
79	4	reporting_effort	2	62	Dataset	SDTM	lb	t	2025-08-14 08:37:28.570481	2025-08-14 08:37:28.570481
80	4	reporting_effort	2	1	TLF	Table	T_14_1_1_DEBUG	t	2025-08-14 08:37:28.59612	2025-08-14 08:37:28.59612
81	4	reporting_effort	2	29	TLF	Table	T_AFTER_RELOAD_1755121385	t	2025-08-14 08:37:28.618128	2025-08-14 08:37:28.618128
82	4	reporting_effort	2	7	TLF	Table	T_API_CHECK_003	t	2025-08-14 08:37:28.640644	2025-08-14 08:37:28.640644
83	4	reporting_effort	2	26	TLF	Table	T_API_TEST_1755121286	t	2025-08-14 08:37:28.657713	2025-08-14 08:37:28.657713
84	4	reporting_effort	2	6	TLF	Table	T_CHECK_001	t	2025-08-14 08:37:28.673507	2025-08-14 08:37:28.673507
85	4	reporting_effort	2	27	TLF	Table	T_DEBUG_1755121327	t	2025-08-14 08:37:28.693258	2025-08-14 08:37:28.693258
86	4	reporting_effort	2	35	TLF	Table	T_DICT_RESPONSE_1755121577	t	2025-08-14 08:37:28.70497	2025-08-14 08:37:28.70497
87	4	reporting_effort	2	25	TLF	Table	T_DIRECT_TEST_88409.656	t	2025-08-14 08:37:28.721387	2025-08-14 08:37:28.721387
88	4	reporting_effort	2	28	TLF	Table	T_FIXED_1755121372	t	2025-08-14 08:37:28.736577	2025-08-14 08:37:28.736577
89	4	reporting_effort	2	34	TLF	Table	T_MINIMAL_1755121531	t	2025-08-14 08:37:28.75222	2025-08-14 08:37:28.75222
90	4	reporting_effort	2	31	TLF	Table	T_NO_AUDIT_1755121437	t	2025-08-14 08:37:28.75222	2025-08-14 08:37:28.75222
91	4	reporting_effort	2	30	TLF	Table	T_NO_WEBSOCKET_1755121419	t	2025-08-14 08:37:28.783965	2025-08-14 08:37:28.783965
92	4	reporting_effort	2	33	TLF	Table	T_SIMPLE_OBJECT_1755121502	t	2025-08-14 08:37:28.783965	2025-08-14 08:37:28.783965
93	4	reporting_effort	2	32	TLF	Table	T_SIMPLE_RESPONSE_1755121452	t	2025-08-14 08:37:28.799754	2025-08-14 08:37:28.799754
94	4	reporting_effort	2	2	TLF	Table	T_TEST_001	t	2025-08-14 08:37:28.822332	2025-08-14 08:37:28.822332
95	4	reporting_effort	2	3	TLF	Table	T_TEST_FINAL_001	t	2025-08-14 08:37:28.831455	2025-08-14 08:37:28.831455
96	4	reporting_effort	2	8	TLF	Table	T_TEST_FIXED	t	2025-08-14 08:37:28.847393	2025-08-14 08:37:28.847393
97	4	reporting_effort	2	4	TLF	Table	T_VERIFY_001	t	2025-08-14 08:37:28.87247	2025-08-14 08:37:28.87247
98	4	reporting_effort	2	5	TLF	Table	T_VERIFY_002	t	2025-08-14 08:37:28.87946	2025-08-14 08:37:28.87946
99	4	reporting_effort	2	42	TLF	Table	T_VERIFY_1755121764	t	2025-08-14 08:37:28.895399	2025-08-14 08:37:28.895399
100	4	reporting_effort	2	65	TLF	Table	t11	t	2025-08-14 08:37:28.911093	2025-08-14 08:37:28.911093
101	4	reporting_effort	2	56	TLF	Table	t14.1.1	t	2025-08-14 08:37:28.927076	2025-08-14 08:37:28.927076
102	4	reporting_effort	2	57	TLF	Table	t14.2.1	t	2025-08-14 08:37:28.942875	2025-08-14 08:37:28.942875
103	4	reporting_effort	2	69	TLF	Table	t20.1.1	t	2025-08-14 08:37:28.95861	2025-08-14 08:37:28.95861
104	4	reporting_effort	2	70	TLF	Table	t99.9.9	t	2025-08-14 08:37:28.974454	2025-08-14 08:37:28.974454
105	4	reporting_effort	2	61	Dataset	SDTM	vs	t	2025-08-14 08:37:28.990208	2025-08-14 08:37:28.990208
141	13	reporting_effort	2	64	Dataset	ADaM	adae	t	2025-08-14 08:43:40.463851	2025-08-14 08:43:40.463851
142	13	reporting_effort	2	67	Dataset	ADaM	adeff	t	2025-08-14 08:43:40.494142	2025-08-14 08:43:40.494142
143	13	reporting_effort	2	63	Dataset	ADaM	adsl	t	2025-08-14 08:43:40.527618	2025-08-14 08:43:40.527618
144	13	reporting_effort	2	60	Dataset	SDTM	ae	t	2025-08-14 08:43:40.544863	2025-08-14 08:43:40.544863
145	13	reporting_effort	2	66	Dataset	SDTM	cm	t	2025-08-14 08:43:40.560537	2025-08-14 08:43:40.560537
146	13	reporting_effort	2	59	Dataset	SDTM	DM	t	2025-08-14 08:43:40.577119	2025-08-14 08:43:40.577119
147	13	reporting_effort	2	68	TLF	Figure	f9.1.1	t	2025-08-14 08:43:40.594169	2025-08-14 08:43:40.594169
148	13	reporting_effort	2	58	TLF	Listing	l16.1.1	t	2025-08-14 08:43:40.613492	2025-08-14 08:43:40.613492
149	13	reporting_effort	2	62	Dataset	SDTM	lb	t	2025-08-14 08:43:40.631042	2025-08-14 08:43:40.631042
150	13	reporting_effort	2	1	TLF	Table	T_14_1_1_DEBUG	t	2025-08-14 08:43:40.64914	2025-08-14 08:43:40.64914
151	13	reporting_effort	2	29	TLF	Table	T_AFTER_RELOAD_1755121385	t	2025-08-14 08:43:40.664386	2025-08-14 08:43:40.664386
152	13	reporting_effort	2	7	TLF	Table	T_API_CHECK_003	t	2025-08-14 08:43:40.679389	2025-08-14 08:43:40.679389
153	13	reporting_effort	2	26	TLF	Table	T_API_TEST_1755121286	t	2025-08-14 08:43:40.694953	2025-08-14 08:43:40.694953
154	13	reporting_effort	2	6	TLF	Table	T_CHECK_001	t	2025-08-14 08:43:40.710837	2025-08-14 08:43:40.710837
155	13	reporting_effort	2	27	TLF	Table	T_DEBUG_1755121327	t	2025-08-14 08:43:40.726723	2025-08-14 08:43:40.726723
156	13	reporting_effort	2	35	TLF	Table	T_DICT_RESPONSE_1755121577	t	2025-08-14 08:43:40.731145	2025-08-14 08:43:40.731145
157	13	reporting_effort	2	25	TLF	Table	T_DIRECT_TEST_88409.656	t	2025-08-14 08:43:40.742451	2025-08-14 08:43:40.742451
158	13	reporting_effort	2	28	TLF	Table	T_FIXED_1755121372	t	2025-08-14 08:43:40.764617	2025-08-14 08:43:40.764617
159	13	reporting_effort	2	34	TLF	Table	T_MINIMAL_1755121531	t	2025-08-14 08:43:40.77429	2025-08-14 08:43:40.77429
160	13	reporting_effort	2	31	TLF	Table	T_NO_AUDIT_1755121437	t	2025-08-14 08:43:40.789948	2025-08-14 08:43:40.789948
161	13	reporting_effort	2	30	TLF	Table	T_NO_WEBSOCKET_1755121419	t	2025-08-14 08:43:40.814859	2025-08-14 08:43:40.814859
162	13	reporting_effort	2	33	TLF	Table	T_SIMPLE_OBJECT_1755121502	t	2025-08-14 08:43:40.831277	2025-08-14 08:43:40.831277
163	13	reporting_effort	2	32	TLF	Table	T_SIMPLE_RESPONSE_1755121452	t	2025-08-14 08:43:40.837676	2025-08-14 08:43:40.837676
164	13	reporting_effort	2	2	TLF	Table	T_TEST_001	t	2025-08-14 08:43:40.853425	2025-08-14 08:43:40.853425
165	13	reporting_effort	2	3	TLF	Table	T_TEST_FINAL_001	t	2025-08-14 08:43:40.86906	2025-08-14 08:43:40.86906
166	13	reporting_effort	2	8	TLF	Table	T_TEST_FIXED	t	2025-08-14 08:43:40.884746	2025-08-14 08:43:40.884746
167	13	reporting_effort	2	4	TLF	Table	T_VERIFY_001	t	2025-08-14 08:43:40.900485	2025-08-14 08:43:40.900485
168	13	reporting_effort	2	5	TLF	Table	T_VERIFY_002	t	2025-08-14 08:43:40.916252	2025-08-14 08:43:40.916252
169	13	reporting_effort	2	42	TLF	Table	T_VERIFY_1755121764	t	2025-08-14 08:43:40.93121	2025-08-14 08:43:40.93121
170	13	reporting_effort	2	65	TLF	Table	t11	t	2025-08-14 08:43:40.932215	2025-08-14 08:43:40.932215
171	13	reporting_effort	2	56	TLF	Table	t14.1.1	t	2025-08-14 08:43:40.948069	2025-08-14 08:43:40.948069
172	13	reporting_effort	2	57	TLF	Table	t14.2.1	t	2025-08-14 08:43:40.965771	2025-08-14 08:43:40.965771
173	13	reporting_effort	2	69	TLF	Table	t20.1.1	t	2025-08-14 08:43:40.99564	2025-08-14 08:43:40.99564
174	13	reporting_effort	2	70	TLF	Table	t99.9.9	t	2025-08-14 08:43:41.011344	2025-08-14 08:43:41.011344
175	13	reporting_effort	2	61	Dataset	SDTM	vs	t	2025-08-14 08:43:41.027209	2025-08-14 08:43:41.027209
176	5	reporting_effort	2	64	Dataset	ADaM	adae	t	2025-08-14 08:48:44.584355	2025-08-14 08:48:44.584355
177	5	reporting_effort	2	67	Dataset	ADaM	adeff	t	2025-08-14 08:48:44.613242	2025-08-14 08:48:44.613242
178	5	reporting_effort	2	63	Dataset	ADaM	adsl	t	2025-08-14 08:48:44.628122	2025-08-14 08:48:44.628122
179	5	reporting_effort	2	60	Dataset	SDTM	ae	t	2025-08-14 08:48:44.646259	2025-08-14 08:48:44.646259
180	5	reporting_effort	2	66	Dataset	SDTM	cm	t	2025-08-14 08:48:44.661852	2025-08-14 08:48:44.661852
181	5	reporting_effort	2	59	Dataset	SDTM	DM	t	2025-08-14 08:48:44.694808	2025-08-14 08:48:44.694808
184	5	reporting_effort	2	62	Dataset	SDTM	lb	t	2025-08-14 08:48:44.745869	2025-08-14 08:48:44.745869
185	5	reporting_effort	2	1	TLF	Table	T_14_1_1_DEBUG	t	2025-08-14 08:48:44.761968	2025-08-14 08:48:44.761968
186	5	reporting_effort	2	29	TLF	Table	T_AFTER_RELOAD_1755121385	t	2025-08-14 08:48:44.780013	2025-08-14 08:48:44.780013
187	5	reporting_effort	2	7	TLF	Table	T_API_CHECK_003	t	2025-08-14 08:48:44.795546	2025-08-14 08:48:44.795546
188	5	reporting_effort	2	26	TLF	Table	T_API_TEST_1755121286	t	2025-08-14 08:48:44.809583	2025-08-14 08:48:44.809583
189	5	reporting_effort	2	6	TLF	Table	T_CHECK_001	t	2025-08-14 08:48:44.824235	2025-08-14 08:48:44.824235
190	5	reporting_effort	2	27	TLF	Table	T_DEBUG_1755121327	t	2025-08-14 08:48:44.838278	2025-08-14 08:48:44.838278
191	5	reporting_effort	2	35	TLF	Table	T_DICT_RESPONSE_1755121577	t	2025-08-14 08:48:44.845366	2025-08-14 08:48:44.845366
192	5	reporting_effort	2	25	TLF	Table	T_DIRECT_TEST_88409.656	t	2025-08-14 08:48:44.860029	2025-08-14 08:48:44.860029
193	5	reporting_effort	2	28	TLF	Table	T_FIXED_1755121372	t	2025-08-14 08:48:44.875895	2025-08-14 08:48:44.875895
194	5	reporting_effort	2	34	TLF	Table	T_MINIMAL_1755121531	t	2025-08-14 08:48:44.895858	2025-08-14 08:48:44.895858
195	5	reporting_effort	2	31	TLF	Table	T_NO_AUDIT_1755121437	t	2025-08-14 08:48:44.918453	2025-08-14 08:48:44.918453
196	5	reporting_effort	2	30	TLF	Table	T_NO_WEBSOCKET_1755121419	t	2025-08-14 08:48:44.934349	2025-08-14 08:48:44.934349
197	5	reporting_effort	2	33	TLF	Table	T_SIMPLE_OBJECT_1755121502	t	2025-08-14 08:48:44.950787	2025-08-14 08:48:44.950787
198	5	reporting_effort	2	32	TLF	Table	T_SIMPLE_RESPONSE_1755121452	t	2025-08-14 08:48:44.963937	2025-08-14 08:48:44.963937
199	5	reporting_effort	2	2	TLF	Table	T_TEST_001	t	2025-08-14 08:48:44.969946	2025-08-14 08:48:44.969946
200	5	reporting_effort	2	3	TLF	Table	T_TEST_FINAL_001	t	2025-08-14 08:48:44.985648	2025-08-14 08:48:44.985648
201	5	reporting_effort	2	8	TLF	Table	T_TEST_FIXED	t	2025-08-14 08:48:45.006907	2025-08-14 08:48:45.006907
202	5	reporting_effort	2	4	TLF	Table	T_VERIFY_001	t	2025-08-14 08:48:45.018327	2025-08-14 08:48:45.018327
203	5	reporting_effort	2	5	TLF	Table	T_VERIFY_002	t	2025-08-14 08:48:45.033551	2025-08-14 08:48:45.033551
204	5	reporting_effort	2	42	TLF	Table	T_VERIFY_1755121764	t	2025-08-14 08:48:45.049686	2025-08-14 08:48:45.049686
205	5	reporting_effort	2	65	TLF	Table	t11	t	2025-08-14 08:48:45.069	2025-08-14 08:48:45.069
206	5	reporting_effort	2	56	TLF	Table	t14.1.1	t	2025-08-14 08:48:45.087284	2025-08-14 08:48:45.087284
207	5	reporting_effort	2	57	TLF	Table	t14.2.1	t	2025-08-14 08:48:45.096704	2025-08-14 08:48:45.096704
208	5	reporting_effort	2	69	TLF	Table	t20.1.1	t	2025-08-14 08:48:45.128784	2025-08-14 08:48:45.128784
209	5	reporting_effort	2	70	TLF	Table	t99.9.9	t	2025-08-14 08:48:45.128784	2025-08-14 08:48:45.128784
210	5	reporting_effort	2	61	Dataset	SDTM	vs	t	2025-08-14 08:48:45.160487	2025-08-14 08:48:45.160487
213	5	reporting_effort	2	68	TLF	Figure	f9.1.1	t	2025-08-14 08:59:01.297328	2025-08-14 08:59:01.297328
214	5	reporting_effort	2	58	TLF	Listing	l16.1.1	t	2025-08-14 08:59:01.368937	2025-08-14 08:59:01.368937
215	2	package	1	10	TLF	Listing	l16.1.1	t	2025-08-14 15:07:17.719755	2025-08-14 15:07:17.719755
216	2	package	1	34	TLF	Figure	f9.1.1	t	2025-08-14 15:07:17.744784	2025-08-14 15:07:17.744784
217	2	package	1	14	Dataset	SDTM	DM	t	2025-08-14 15:07:41.920408	2025-08-14 15:07:41.920408
218	2	package	1	16	Dataset	SDTM	ae	t	2025-08-14 15:07:41.936854	2025-08-14 15:07:41.936854
231	20	\N	\N	\N	TLF	Table	14.1.1	t	2025-08-18 07:23:01.416238	2025-08-18 07:23:01.416238
232	21	\N	\N	\N	TLF	Table	14.1.1	t	2025-08-18 07:24:13.341206	2025-08-18 07:24:13.341206
233	22	\N	\N	\N	TLF	Table	14.1.1	t	2025-08-18 07:24:28.385388	2025-08-18 07:24:28.385388
234	23	\N	\N	\N	TLF	Table	14.1.1	t	2025-08-18 07:24:53.409182	2025-08-18 07:24:53.409182
235	23	\N	\N	\N	TLF	Table	14.2.1	t	2025-08-18 07:24:53.423564	2025-08-18 07:24:53.423564
236	23	\N	\N	\N	TLF	Figure	14.3.1	t	2025-08-18 07:24:53.429805	2025-08-18 07:24:53.429805
237	23	\N	\N	\N	TLF	Listing	16.2.1	t	2025-08-18 07:24:53.435233	2025-08-18 07:24:53.435233
238	23	\N	\N	\N	Dataset	SDTM	DM	t	2025-08-18 07:24:53.441072	2025-08-18 07:24:53.441072
239	23	\N	\N	\N	Dataset	SDTM	AE	t	2025-08-18 07:24:53.447314	2025-08-18 07:24:53.447314
240	23	\N	\N	\N	Dataset	ADaM	ADSL	t	2025-08-18 07:24:53.452687	2025-08-18 07:24:53.452687
241	23	\N	\N	\N	Dataset	ADaM	ADEFF	t	2025-08-18 07:24:53.457555	2025-08-18 07:24:53.457555
\.


--
-- Data for Name: reporting_effort_tlf_details; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_effort_tlf_details (id, reporting_effort_item_id, title_id, population_flag_id, ich_category_id) FROM stdin;
1	56	4	8	5
2	57	9	10	11
4	65	4	8	5
6	69	22	8	11
7	70	43	\N	\N
8	77	42	8	\N
9	78	16	17	18
10	100	4	8	5
11	101	4	8	5
12	102	9	10	11
13	103	22	8	11
14	104	43	\N	\N
22	147	42	8	\N
23	148	16	17	18
24	170	4	8	5
25	171	4	8	5
26	172	9	10	11
27	173	22	8	11
28	174	43	\N	\N
31	205	4	8	5
32	206	4	8	5
33	207	9	10	11
34	208	22	8	11
35	209	43	\N	\N
38	213	42	8	\N
39	214	16	17	18
40	215	16	17	18
41	216	42	8	\N
\.


--
-- Data for Name: reporting_efforts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_efforts (id, study_id, database_release_id, database_release_label, created_at, updated_at) FROM stdin;
2	3	1	test_re_1	2025-08-09 17:39:41.018238	2025-08-09 17:39:41.018238
4	7	2	103_re	2025-08-10 22:45:27.144987	2025-08-10 22:45:27.144987
5	2	11	test	2025-08-11 16:44:05.208266	2025-08-11 16:44:05.208266
13	19	20	Debug Reporting Effort	2025-08-13 21:38:51.292615	2025-08-13 21:38:51.292615
17	25	24	Test Reporting Effort	2025-08-18 05:06:39.405864	2025-08-18 05:06:39.405864
20	32	27	CSR Primary Analysis - January 2025	2025-08-18 07:23:01.36371	2025-08-18 07:23:01.36371
21	33	28	CSR Primary Analysis - January 2025	2025-08-18 07:24:13.301648	2025-08-18 07:24:13.301648
22	34	29	CSR Primary Analysis - January 2025	2025-08-18 07:24:28.353986	2025-08-18 07:24:28.353986
23	35	30	CSR Primary Analysis - January 2025	2025-08-18 07:24:53.364016	2025-08-18 07:24:53.364016
\.


--
-- Data for Name: studies; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.studies (id, study_label, created_at, updated_at) FROM stdin;
5	ag102	2025-08-10 20:48:33.708033	2025-08-10 20:48:33.708033
7	ag103	2025-08-10 22:40:20.542898	2025-08-10 22:40:20.542898
8	ag104s	2025-08-10 22:49:59.115761	2025-08-10 22:50:34.72034
3	aTest Study	2025-08-09 17:23:43.108091	2025-08-11 20:29:33.954462
4	abc123z	2025-08-09 17:31:59.527167	2025-08-11 20:35:38.749066
2	atesting	2025-08-09 17:20:53.227283	2025-08-11 20:52:49.962038
18	Debug Test Study	2025-08-13 21:38:13.627918	2025-08-13 21:38:13.627918
19	Debug Test Study 1755121120	2025-08-13 21:38:40.945979	2025-08-13 21:38:40.945979
25	Test Study for Comments	2025-08-18 05:06:18.482819	2025-08-18 05:06:18.482819
32	PEARL-2025-001	2025-08-18 07:23:01.347161	2025-08-18 07:23:01.347161
33	PEARL-2025-001	2025-08-18 07:24:13.274057	2025-08-18 07:24:13.274057
34	PEARL-2025-001	2025-08-18 07:24:28.333805	2025-08-18 07:24:28.333805
35	PEARL-2025-001	2025-08-18 07:24:53.346226	2025-08-18 07:24:53.346226
\.


--
-- Data for Name: text_elements; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.text_elements (id, type, label, created_at, updated_at) FROM stdin;
4	title	Summary of Demographics	2025-08-11 21:21:08.558615	2025-08-11 21:21:08.558615
5	ich_category	E2A	2025-08-12 03:22:19.928431	2025-08-12 03:22:19.928431
7	footnote	Baseline defined as Day 1	2025-08-12 03:22:57.441729	2025-08-12 03:22:57.441729
8	population_set	ITT Population	2025-08-12 03:25:21.669039	2025-08-12 03:25:21.669039
9	title	Summary of Adverse Events	2025-08-12 03:27:13.784113	2025-08-12 03:27:13.784113
10	population_set	Safety Population	2025-08-12 03:27:13.796114	2025-08-12 03:27:13.796114
11	ich_category	E3	2025-08-12 03:27:13.801468	2025-08-12 03:27:13.801468
12	footnote	Includes all treatment-emergent events	2025-08-12 03:27:13.804467	2025-08-12 03:27:13.804467
13	footnote	Safety population	2025-08-12 03:27:13.809014	2025-08-12 03:27:13.809014
14	acronyms_set	AE = Adverse Event	2025-08-12 03:27:13.813492	2025-08-12 03:27:13.813492
15	acronyms_set	SAE = Serious Adverse Event	2025-08-12 03:27:13.81802	2025-08-12 03:27:13.81802
16	title	Patient Listings	2025-08-12 03:27:13.849867	2025-08-12 03:27:13.849867
17	population_set	All Enrolled	2025-08-12 03:27:13.852951	2025-08-12 03:27:13.852951
18	ich_category	E2B	2025-08-12 03:27:13.856955	2025-08-12 03:27:13.856955
19	footnote	Sorted by patient ID	2025-08-12 03:27:13.859951	2025-08-12 03:27:13.859951
20	title	Kaplan-Meier Survival Curve	2025-08-12 03:27:13.876217	2025-08-12 03:27:13.876217
21	acronyms_set	CI = Confidence Interval	2025-08-12 03:27:13.880216	2025-08-12 03:27:13.880216
22	title	Efficacy Summary	2025-08-12 03:28:45.01982	2025-08-12 03:28:45.01982
23	footnote	Based on ITT analysis	2025-08-12 03:28:45.034516	2025-08-12 03:28:45.034516
24	title	Forest Plot	2025-08-12 03:28:45.051309	2025-08-12 03:28:45.051309
25	acronyms_set	HR = Hazard Ratio	2025-08-12 03:28:45.051309	2025-08-12 03:28:45.051309
26	title	Test Title	2025-08-12 03:30:49.051248	2025-08-12 03:30:49.051248
27	title	Test Title 2	2025-08-12 03:30:49.399819	2025-08-12 03:30:49.399819
28	population_set	Test Population	2025-08-12 03:30:49.504668	2025-08-12 03:30:49.504668
29	population_set	Test Population 2	2025-08-12 03:30:49.814179	2025-08-12 03:30:49.814179
30	ich_category	E6	2025-08-12 03:30:49.933197	2025-08-12 03:30:49.933197
31	ich_category	E7	2025-08-12 03:30:50.245286	2025-08-12 03:30:50.245286
6	footnote	Data includes all subjects with baseline and post baseline	2025-08-12 03:22:57.314919	2025-08-12 04:02:44.576839
32	title	Primary Efficacy Endpoint Analysis	2025-08-12 04:27:45.276053	2025-08-12 04:27:45.276053
33	title	Safety Population Summary	2025-08-12 04:27:45.317013	2025-08-12 04:27:45.317013
34	footnote	Data cutoff date: December 31, 2024	2025-08-12 04:27:45.33933	2025-08-12 04:27:45.33933
35	footnote	ITT = Intention to Treat population	2025-08-12 04:27:45.361235	2025-08-12 04:27:45.361235
36	population_set	All randomized patients who received at least one dose	2025-08-12 04:27:45.383713	2025-08-12 04:27:45.383713
37	population_set	Per Protocol population excluding major protocol violations	2025-08-12 04:27:45.41648	2025-08-12 04:27:45.41648
38	acronyms_set	AE = Adverse Event; SAE = Serious Adverse Event	2025-08-12 04:27:45.437415	2025-08-12 04:27:45.437415
39	ich_category	ICH E3 Section 11.4.2.1 - Demographic and Baseline Characteristics	2025-08-12 04:27:45.4588	2025-08-12 04:27:45.4588
40	footnote	Pvalue is calculated from cox hazard model.	2025-08-12 04:32:26.554089	2025-08-12 04:32:26.554089
41	title	Summary of Efficacy	2025-08-12 06:35:58.779544	2025-08-12 06:35:58.779544
42	title	Kaplan-Meier Survival	2025-08-12 06:35:58.918152	2025-08-12 06:35:58.918152
43	title	Test Table	2025-08-12 07:50:32.110762	2025-08-12 07:50:32.110762
\.


--
-- Data for Name: tracker_comments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tracker_comments (id, tracker_id, user_id, parent_comment_id, comment_text, is_resolved, resolved_by_user_id, resolved_at, created_at, updated_at) FROM stdin;
1	2	1	\N	FRESH START: Parent comment with clean database	f	\N	\N	2025-08-18 00:47:36.869414-04	2025-08-18 00:47:36.869414-04
2	2	1	\N	Reply to comment 1	f	\N	\N	2025-08-18 00:49:13.966084-04	2025-08-18 00:49:13.966084-04
3	2	1	\N	DEBUG: Reply with parent_comment_id=1	f	\N	\N	2025-08-18 00:49:54.757162-04	2025-08-18 00:49:54.757162-04
4	2	1	\N	DEBUG: Test with parent_comment_id=1	f	\N	\N	2025-08-18 00:50:18.254545-04	2025-08-18 00:50:18.254545-04
6	2	1	\N	This is a simplified blog-style comment	t	1	2025-08-18 01:08:20.180974-04	2025-08-18 01:08:19.64963-04	2025-08-18 01:08:20.180974-04
7	2	1	\N	Another comment to test button state	f	\N	\N	2025-08-18 01:08:20.387157-04	2025-08-18 01:08:20.387157-04
8	2	1	6	This is a reply to comment 6	f	\N	\N	2025-08-18 01:09:05.750588-04	2025-08-18 01:09:05.750588-04
10	214	1	9	testing	f	\N	\N	2025-08-18 01:20:32.589516-04	2025-08-18 01:20:32.589516-04
28	214	1	\N	new comment	t	1	2025-08-18 13:50:15.780281-04	2025-08-18 11:35:52.493138-04	2025-08-18 13:50:15.780281-04
9	214	1	\N	test	t	1	2025-08-18 01:20:55.859424-04	2025-08-18 01:20:12.873228-04	2025-08-18 01:20:55.859424-04
13	213	1	12	reply to first comment	f	\N	\N	2025-08-18 01:47:07.923198-04	2025-08-18 01:47:07.923198-04
56	25	1	\N	tezt	f	\N	\N	2025-08-18 13:50:34.2527-04	2025-08-18 13:50:34.2527-04
12	213	1	\N	first comment	t	1	2025-08-18 01:47:54.860611-04	2025-08-18 01:46:54.707379-04	2025-08-18 01:47:54.860611-04
14	213	1	12	another reply	f	\N	\N	2025-08-18 01:51:04.713556-04	2025-08-18 01:51:04.713556-04
15	28	1	\N	testing	f	\N	\N	2025-08-18 01:53:31.594742-04	2025-08-18 01:53:31.594742-04
16	28	1	15	replying	f	\N	\N	2025-08-18 01:53:46.802926-04	2025-08-18 01:53:46.802926-04
17	2	1	\N	Test comment from curl	f	\N	\N	2025-08-18 02:27:28.379201-04	2025-08-18 02:27:28.379201-04
24	75	1	23	answer to first comment	f	\N	\N	2025-08-18 11:25:06.603059-04	2025-08-18 11:25:06.603059-04
25	75	1	23	another answer to fist comment	f	\N	\N	2025-08-18 11:25:23.908528-04	2025-08-18 11:25:23.908528-04
26	75	1	25	third level comment	f	\N	\N	2025-08-18 11:25:40.362558-04	2025-08-18 11:25:40.362558-04
30	76	1	\N	first comment	f	\N	\N	2025-08-18 11:37:01.202496-04	2025-08-18 11:37:01.202496-04
31	76	1	\N	second comment	f	\N	\N	2025-08-18 11:37:07.760986-04	2025-08-18 11:37:07.760986-04
32	76	1	\N	third comment	f	\N	\N	2025-08-18 11:37:14.620765-04	2025-08-18 11:37:14.620765-04
33	76	1	32	replying third comment	f	\N	\N	2025-08-18 11:37:33.244354-04	2025-08-18 11:37:33.244354-04
34	76	1	\N	fourth comment	t	1	2025-08-18 11:38:10.946133-04	2025-08-18 11:37:55.332256-04	2025-08-18 11:38:10.946133-04
35	76	1	\N	This is an unresolved test comment that should make the button yellow	f	\N	\N	2025-08-18 11:39:52.560323-04	2025-08-18 11:39:52.560323-04
36	145	1	\N	This is a test comment to verify the comment badge functionality works correctly.	f	\N	\N	2025-08-18 11:49:15.06624-04	2025-08-18 11:49:15.06624-04
37	145	1	\N	another comment to see yellow button	f	\N	\N	2025-08-18 11:51:25.582455-04	2025-08-18 11:51:25.582455-04
38	146	1	\N	cross browser check	f	\N	\N	2025-08-18 11:53:55.477006-04	2025-08-18 11:53:55.477006-04
39	145	1	\N	Testing real-time cross-browser comment badge updates via WebSocket! This should trigger a badge update in all connected browser sessions.	f	\N	\N	2025-08-18 12:01:33.108075-04	2025-08-18 12:01:33.108075-04
40	145	1	\N	WebSocket routing fix test - this should update badge counts in all browser sessions!	f	\N	\N	2025-08-18 12:04:51.143044-04	2025-08-18 12:04:51.143044-04
41	145	1	\N	CACHE CLEAR TEST: Testing that the latest WebSocket client JS code is loaded after clearing browser cache. This comment should trigger proper routing to reporting_effort_tracker module and update badges immediately!	f	\N	\N	2025-08-18 12:08:15.725699-04	2025-08-18 12:08:15.725699-04
42	145	1	\N	SERVER RESTART TEST: This comment should trigger the CORRECT WebSocket routing message - looking for 'routing to reporting_effort_tracker' instead of 'using periodic refresh'. Testing real-time badge updates!	f	\N	\N	2025-08-18 12:11:41.203815-04	2025-08-18 12:11:41.203815-04
43	145	1	\N	CACHE-BUSTING TEST SUCCESS: This comment verifies that the updated WebSocket client code is now properly loaded via cache-busting parameter. Should trigger real-time badge update from +6 to +7!	f	\N	\N	2025-08-18 12:14:17.895389-04	2025-08-18 12:14:17.895389-04
44	148	1	\N	new	f	\N	\N	2025-08-18 12:15:27.945936-04	2025-08-18 12:15:27.945936-04
45	145	1	\N	CLEANED WEBSOCKET TEST: Testing the cleaned up WebSocket implementation that removed all duplicate observers and experimental code. This comment should trigger a single, clean WebSocket event that updates the badge from +7 to +8 immediately!	f	\N	\N	2025-08-18 12:19:29.22822-04	2025-08-18 12:19:29.22822-04
46	145	1	\N	FINAL TEST COMMENT: This is the ultimate test of our cleaned up comment system! This should increment the badge from +8 to +9 and broadcast the update via WebSocket to any other connected browser sessions. The cleanup was successful!	f	\N	\N	2025-08-18 12:23:55.596282-04	2025-08-18 12:23:55.596282-04
47	149	1	\N	test	f	\N	\N	2025-08-18 12:36:55.59804-04	2025-08-18 12:36:55.59804-04
48	149	1	\N	it should be 2 now	f	\N	\N	2025-08-18 12:40:22.039077-04	2025-08-18 12:40:22.039077-04
11	214	1	\N	first comment	t	1	2025-08-18 12:46:46.087319-04	2025-08-18 01:21:31.076384-04	2025-08-18 12:46:46.087319-04
19	214	1	\N	Test comment from debugging	t	1	2025-08-18 12:46:54.717637-04	2025-08-18 02:48:13.72199-04	2025-08-18 12:46:54.717637-04
49	213	1	\N	Testing real-time comment badge updates via WebSocket	f	\N	\N	2025-08-18 12:53:40.306605-04	2025-08-18 12:53:40.306605-04
50	78	1	\N	3rd	f	\N	\N	2025-08-18 12:57:15.554261-04	2025-08-18 12:57:15.554261-04
23	75	1	\N	first comment	t	1	2025-08-18 12:59:39.523195-04	2025-08-18 11:24:53.524024-04	2025-08-18 12:59:39.523195-04
51	214	1	\N	new	f	\N	\N	2025-08-18 13:06:37.426511-04	2025-08-18 13:06:37.426511-04
52	214	1	\N	WebSocket test comment - this should update all browsers in real-time!	f	\N	\N	2025-08-18 13:24:07.108294-04	2025-08-18 13:24:07.108294-04
27	214	1	\N	Testing comment system with Playwright - this should trigger badge update	t	1	2025-08-18 13:26:43.164949-04	2025-08-18 11:34:08.588897-04	2025-08-18 13:26:43.164949-04
29	214	1	\N	new comment	t	1	2025-08-18 13:51:43.678831-04	2025-08-18 11:36:23.905555-04	2025-08-18 13:51:43.678831-04
57	6	1	\N	test	f	\N	\N	2025-08-18 13:52:01.180668-04	2025-08-18 13:52:01.180668-04
54	214	1	\N	Testing automatic WebSocket updates with debug logging - button should change from +4 to +5 automatically!	t	1	2025-08-18 13:53:17.582116-04	2025-08-18 13:39:33.35981-04	2025-08-18 13:53:17.582116-04
58	6	1	\N	LIVE WebSocket Test - this should automatically update button from +1 to +2 in real-time!	f	\N	\N	2025-08-18 13:55:14.953259-04	2025-08-18 13:55:14.953259-04
55	214	1	\N	Testing namespace fix - this comment should trigger automatic +5 to +6 button update via WebSocket!	t	1	2025-08-18 14:21:11.523807-04	2025-08-18 13:48:49.180973-04	2025-08-18 14:21:11.523807-04
59	25	1	\N	new	f	\N	\N	2025-08-18 14:21:30.060091-04	2025-08-18 14:21:30.060091-04
60	6	1	\N	three	f	\N	\N	2025-08-18 14:22:02.4699-04	2025-08-18 14:22:02.4699-04
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, role, department) FROM stdin;
2	vgaddu	ADMIN	\N
3	jjohn	VIEWER	\N
1	test_administrators	ADMIN	\N
9	kmist	VIEWER	\N
12	jane.smith	EDITOR	\N
11	john.doe	ADMIN	\N
35	tracker-comment-test-1755276165-user	EDITOR	\N
36	tracker-comment-test-1755412771-user	EDITOR	\N
37	tracker-comment-test-1755417434-user	EDITOR	\N
44	john_smith	EDITOR	\N
45	jane_doe	EDITOR	\N
46	bob_wilson	VIEWER	\N
47	alice_johnson	EDITOR	\N
13	admin.user	ADMIN	management
\.


--
-- Name: audit_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.audit_log_id_seq', 112, true);


--
-- Name: database_releases_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.database_releases_id_seq', 32, true);


--
-- Name: package_dataset_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.package_dataset_details_id_seq', 12, true);


--
-- Name: package_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.package_items_id_seq', 37, true);


--
-- Name: package_tlf_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.package_tlf_details_id_seq', 19, true);


--
-- Name: packages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.packages_id_seq', 10, true);


--
-- Name: reporting_effort_dataset_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reporting_effort_dataset_details_id_seq', 42, true);


--
-- Name: reporting_effort_item_tracker_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reporting_effort_item_tracker_id_seq', 216, true);


--
-- Name: reporting_effort_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reporting_effort_items_id_seq', 245, true);


--
-- Name: reporting_effort_tlf_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reporting_effort_tlf_details_id_seq', 41, true);


--
-- Name: reporting_efforts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reporting_efforts_id_seq', 25, true);


--
-- Name: studies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.studies_id_seq', 37, true);


--
-- Name: text_elements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.text_elements_id_seq', 45, true);


--
-- Name: tracker_comments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tracker_comments_id_seq', 60, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 49, true);


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

CREATE INDEX ix_studies_study_label ON public.studies USING btree (study_label);


--
-- Name: ix_text_elements_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_text_elements_type ON public.text_elements USING btree (type);


--
-- Name: ix_tracker_comments_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tracker_comments_id ON public.tracker_comments USING btree (id);


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
-- PostgreSQL database dump complete
--

