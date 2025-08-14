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
    item_type public.itemtype NOT NULL,
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
    production_status character varying(50),
    due_date date,
    priority character varying(50),
    qc_level character varying(50),
    qc_programmer_id integer,
    qc_status character varying(50),
    qc_completion_date date,
    in_production_flag boolean,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
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
    source_type character varying(50),
    source_id integer,
    source_item_id integer,
    item_type public.itemtype NOT NULL,
    item_subtype character varying(50) NOT NULL,
    item_code character varying(255) NOT NULL,
    is_active boolean,
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
-- Name: reporting_effort_tracker_comments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reporting_effort_tracker_comments (
    id integer NOT NULL,
    tracker_id integer NOT NULL,
    user_id integer NOT NULL,
    parent_comment_id integer,
    comment_text text NOT NULL,
    comment_type character varying(50),
    comment_category character varying(50),
    is_pinned boolean,
    is_edited boolean,
    edited_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.reporting_effort_tracker_comments OWNER TO postgres;

--
-- Name: reporting_effort_tracker_comments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.reporting_effort_tracker_comments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reporting_effort_tracker_comments_id_seq OWNER TO postgres;

--
-- Name: reporting_effort_tracker_comments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.reporting_effort_tracker_comments_id_seq OWNED BY public.reporting_effort_tracker_comments.id;


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
-- Name: reporting_effort_tracker_comments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_tracker_comments ALTER COLUMN id SET DEFAULT nextval('public.reporting_effort_tracker_comments_id_seq'::regclass);


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
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
0b87c8f59a0e
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

COPY public.reporting_effort_item_tracker (id, reporting_effort_item_id, production_programmer_id, production_status, due_date, priority, qc_level, qc_programmer_id, qc_status, qc_completion_date, in_production_flag, created_at, updated_at) FROM stdin;
1	1	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 20:36:10.518172	2025-08-13 20:36:10.518172
2	2	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:04:02.365308	2025-08-13 21:04:02.365308
3	3	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:07:56.183836	2025-08-13 21:07:56.183836
4	4	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:10:15.96671	2025-08-13 21:10:15.96671
5	5	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:11:25.854159	2025-08-13 21:11:25.854159
6	6	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:16:42.179738	2025-08-13 21:16:42.179738
7	7	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:26:20.762301	2025-08-13 21:26:20.762301
8	8	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:36:36.018635	2025-08-13 21:36:36.018635
21	21	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:38:56.166746	2025-08-13 21:38:56.166746
22	23	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:39:19.666478	2025-08-13 21:39:19.666478
23	24	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:40:09.280318	2025-08-13 21:40:09.280318
24	25	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:40:26.694174	2025-08-13 21:40:26.694174
25	26	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:41:26.980814	2025-08-13 21:41:26.980814
26	27	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:42:07.239602	2025-08-13 21:42:07.239602
27	28	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:42:52.619689	2025-08-13 21:42:52.619689
28	29	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:43:05.865124	2025-08-13 21:43:05.865124
29	30	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:43:39.859682	2025-08-13 21:43:39.859682
30	31	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:43:57.565414	2025-08-13 21:43:57.565414
31	32	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:44:12.612571	2025-08-13 21:44:12.612571
32	33	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:45:02.549642	2025-08-13 21:45:02.549642
33	34	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:45:31.947447	2025-08-13 21:45:31.947447
34	35	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:46:17.525731	2025-08-13 21:46:17.525731
41	42	\N	not_started	\N	medium	\N	\N	not_started	\N	f	2025-08-13 21:49:24.749327	2025-08-13 21:49:24.749327
\.


--
-- Data for Name: reporting_effort_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_effort_items (id, reporting_effort_id, source_type, source_id, source_item_id, item_type, item_subtype, item_code, is_active, created_at, updated_at) FROM stdin;
1	2	\N	\N	\N	TLF	Table	T_14_1_1_DEBUG	t	2025-08-13 20:36:10.502103	2025-08-13 20:36:10.502103
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
\.


--
-- Data for Name: reporting_effort_tlf_details; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_effort_tlf_details (id, reporting_effort_item_id, title_id, population_flag_id, ich_category_id) FROM stdin;
\.


--
-- Data for Name: reporting_effort_tracker_comments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_effort_tracker_comments (id, tracker_id, user_id, parent_comment_id, comment_text, comment_type, comment_category, is_pinned, is_edited, edited_at, created_at) FROM stdin;
\.


--
-- Data for Name: reporting_efforts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reporting_efforts (id, study_id, database_release_id, database_release_label, created_at, updated_at) FROM stdin;
2	3	1	test_re_1	2025-08-09 17:39:41.018238	2025-08-09 17:39:41.018238
4	7	2	103_re	2025-08-10 22:45:27.144987	2025-08-10 22:45:27.144987
5	2	11	test	2025-08-11 16:44:05.208266	2025-08-11 16:44:05.208266
13	19	20	Debug Reporting Effort	2025-08-13 21:38:51.292615	2025-08-13 21:38:51.292615
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
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, role, department) FROM stdin;
2	vgaddu	ADMIN	\N
3	jjohn	VIEWER	\N
1	test_administrators	ADMIN	\N
9	kmist	VIEWER	\N
12	jane.smith	EDITOR	\N
13	admin.user	ADMIN	\N
11	john.doe	ADMIN	\N
\.


--
-- Name: audit_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.audit_log_id_seq', 43, true);


--
-- Name: database_releases_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.database_releases_id_seq', 23, true);


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

SELECT pg_catalog.setval('public.reporting_effort_dataset_details_id_seq', 1, false);


--
-- Name: reporting_effort_item_tracker_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reporting_effort_item_tracker_id_seq', 53, true);


--
-- Name: reporting_effort_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reporting_effort_items_id_seq', 54, true);


--
-- Name: reporting_effort_tlf_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reporting_effort_tlf_details_id_seq', 1, false);


--
-- Name: reporting_effort_tracker_comments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reporting_effort_tracker_comments_id_seq', 1, false);


--
-- Name: reporting_efforts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reporting_efforts_id_seq', 16, true);


--
-- Name: studies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.studies_id_seq', 22, true);


--
-- Name: text_elements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.text_elements_id_seq', 45, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 34, true);


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
-- Name: reporting_effort_tracker_comments reporting_effort_tracker_comments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_tracker_comments
    ADD CONSTRAINT reporting_effort_tracker_comments_pkey PRIMARY KEY (id);


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
-- Name: ix_reporting_effort_tracker_comments_comment_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_reporting_effort_tracker_comments_comment_type ON public.reporting_effort_tracker_comments USING btree (comment_type);


--
-- Name: ix_reporting_effort_tracker_comments_tracker_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_reporting_effort_tracker_comments_tracker_id ON public.reporting_effort_tracker_comments USING btree (tracker_id);


--
-- Name: ix_reporting_effort_tracker_comments_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_reporting_effort_tracker_comments_user_id ON public.reporting_effort_tracker_comments USING btree (user_id);


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
-- Name: reporting_effort_tracker_comments reporting_effort_tracker_comments_parent_comment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_tracker_comments
    ADD CONSTRAINT reporting_effort_tracker_comments_parent_comment_id_fkey FOREIGN KEY (parent_comment_id) REFERENCES public.reporting_effort_tracker_comments(id);


--
-- Name: reporting_effort_tracker_comments reporting_effort_tracker_comments_tracker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_tracker_comments
    ADD CONSTRAINT reporting_effort_tracker_comments_tracker_id_fkey FOREIGN KEY (tracker_id) REFERENCES public.reporting_effort_item_tracker(id);


--
-- Name: reporting_effort_tracker_comments reporting_effort_tracker_comments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reporting_effort_tracker_comments
    ADD CONSTRAINT reporting_effort_tracker_comments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


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
-- PostgreSQL database dump complete
--

