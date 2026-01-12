// ==================== Core Entity Types ====================

export interface Study {
  id: number
  study_label: string
  created_at: string
  updated_at: string
}

export interface DatabaseRelease {
  id: number
  study_id: number
  database_release_label: string
  database_release_date: string
  created_at: string
  updated_at: string
}

// ==================== Use Case Types ====================

export interface UseCase {
  id: number
  name: string
  color: string
  description?: string
  created_at: string
  updated_at: string
  usage_count?: number
}

export interface UseCaseSummary {
  id: number
  name: string
  color: string
}

export interface UseCaseFormData {
  name: string
  color: string
  description?: string
}

export interface BulkUseCaseAssignment {
  reporting_effort_ids: number[]
  use_case_id: number
}

export interface ReportingEffort {
  id: number
  study_id: number
  database_release_id: number
  database_release_label: string
  use_cases?: UseCaseSummary[]
  created_at: string
  updated_at: string
  // Expanded fields for better filtering
  study_label?: string
  database_release_label_full?: string
}

export interface User {
  id: number
  username: string
  email?: string
  is_admin: boolean
  department?: string
  auth_provider?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// ==================== Study-Scoped Access Control Types ====================

export type StudyRole = 'VIEWER' | 'EDITOR' | 'LEAD'

export interface UserStudyRole {
  id: number
  user_id: number
  study_id: number
  role: StudyRole
  created_at: string
  updated_at: string
}

export interface StudyMember {
  id: number
  username: string
  email?: string
  role: StudyRole
  is_admin: boolean
  is_explicit_assignment: boolean
  assigned_at?: string
}

export interface StudyMembersResponse {
  study_id: number
  study_label: string
  members: StudyMember[]
  total_count: number
}

export interface StudyPermissions {
  study_id: number
  role: StudyRole
  can_view: boolean
  can_edit: boolean
  can_bulk_assign: boolean
  can_bulk_status_update: boolean
  can_delete_items: boolean
  can_manage_members: boolean
  can_bulk_copy: boolean
  can_manage_packages: boolean
  can_manage_tfl_properties: boolean
}

export interface MyStudyRolesResponse {
  is_admin: boolean
  lead_study_ids: number[]
  study_roles: Record<number, StudyRole>
}

export interface AssignStudyRoleRequest {
  user_id: number
  role: StudyRole
}

// ==================== Text Element Types ====================

export type TextElementType = 'title' | 'footnote' | 'population_set' | 'acronyms_set' | 'ich_category'

export interface TextElement {
  id: number
  type: TextElementType
  label: string
  content?: string
  created_at: string
  updated_at: string
  usage_count?: number
  is_used?: boolean
}

// ==================== Package Types ====================

export interface Package {
  id: number
  package_name: string
  study_indication?: string
  therapeutic_area?: string
  created_at: string
  updated_at: string
}

export type ItemType = 'TLF' | 'Dataset'
export type ItemSubtype = 'Table' | 'Listing' | 'Figure' | 'SDTM' | 'ADaM'

export interface PackageItem {
  id: number
  package_id: number
  item_code: string
  item_description?: string
  item_type: ItemType
  item_subtype?: ItemSubtype
  created_at: string
  updated_at: string
  tlf_details?: TLFDetails
  dataset_details?: DatasetDetails
  footnotes?: PackageItemFootnote[]
  acronyms?: PackageItemAcronym[]
}

export interface TLFDetails {
  id?: number
  package_item_id?: number
  title_id?: number
  population_flag_id?: number
  ich_category_id?: number
  title?: TextElement
}

export interface DatasetDetails {
  id?: number
  package_item_id?: number
  reporting_effort_item_id?: number
  label?: string
  sorting_order?: number
  ig_version_id?: number
  ig_version?: IGVersion
}

export interface PackageItemFootnote {
  footnote_id: number
  sequence_number?: number
}

export interface PackageItemAcronym {
  acronym_id: number
}

export interface PackageItemCreateWithDetails {
  package_id: number
  item_type: ItemType
  item_subtype: string
  item_code: string
  tlf_details?: Omit<TLFDetails, 'id' | 'package_item_id'>
  dataset_details?: Omit<DatasetDetails, 'id' | 'package_item_id'>
  footnotes?: PackageItemFootnote[]
  acronyms?: PackageItemAcronym[]
}

export interface PackageItemUpdateWithDetails {
  item_type?: ItemType
  item_subtype?: string
  item_code?: string
  tlf_details?: Omit<TLFDetails, 'id' | 'package_item_id'>
  dataset_details?: Omit<DatasetDetails, 'id' | 'package_item_id'>
  footnotes?: PackageItemFootnote[]
  acronyms?: PackageItemAcronym[]
}

// ==================== Reporting Effort Item Types ====================

export interface ReportingEffortItem {
  id: number
  reporting_effort_id: number
  item_code: string
  item_description?: string
  item_type: ItemType
  item_subtype?: ItemSubtype
  dataset_details?: DatasetDetails
  tlf_details?: TLFDetails
  created_at: string
  updated_at: string
}

// ==================== Implementation Guide Version Types ====================

export interface IGVersion {
  id: number
  standard_type: 'SDTM' | 'ADaM'
  version: string
  description?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// ==================== Tracker Types ====================

// Production statuses: not_started → in_progress → ready_for_qc → completed (auto)
// QC statuses: not_started → in_progress → failed/completed
export type ProductionStatus = 'not_started' | 'in_progress' | 'ready_for_qc' | 'completed' | 'on_hold'
export type QCStatus = 'not_started' | 'in_progress' | 'failed' | 'completed' | 'on_hold'
export type TrackerStatus = ProductionStatus | QCStatus  // Union type for backward compatibility
export type Priority = 'critical' | 'high' | 'medium' | 'low'

export interface TrackerTag {
  id: number
  name: string
  color: string
  description?: string
  created_at: string
  updated_at: string
  usage_count?: number
}

export interface TrackerTagSummary {
  id: number
  name: string
  color: string
}

// Milestone info for tracker items
export type MilestoneLinkType = 'subtype' | 'tag' | 'manual'

export interface TrackerMilestoneInfo {
  milestone_id: number
  milestone_name: string
  milestone_due_date?: string
  is_past_due: boolean
  link_type: MilestoneLinkType
}

export interface ReportingEffortItemTracker {
  id: number
  reporting_effort_item_id: number
  production_programmer_id?: number
  qc_programmer_id?: number
  production_status: ProductionStatus
  qc_status: QCStatus
  priority?: Priority
  due_date?: string
  qc_completion_date?: string
  in_production_flag?: boolean
  created_at: string
  updated_at: string
  // Expanded fields
  item_code?: string
  item_title?: string  // Consolidated: TLF title, dataset label, or item description
  item_type?: ItemType
  item_subtype?: ItemSubtype
  production_programmer?: User
  qc_programmer?: User
  comment_count?: number
  unresolved_comment_count?: number
  tags?: TrackerTagSummary[]
  milestones?: TrackerMilestoneInfo[]
  // Study/Reporting Effort context (returned by getAll API)
  reporting_effort_id?: number
  reporting_effort_label?: string
  study_id?: number
  study_label?: string
  database_release_label?: string
}

// Status history for time tracking
export interface TrackerStatusHistory {
  id: number
  status_field: 'production' | 'qc'
  status_value: string
  entered_at: string
  exited_at?: string
  duration_seconds?: number
  changed_by_username?: string
}

// Permissions for a tracker (what the current user can modify)
export interface TrackerPermissions {
  production_status: boolean
  qc_status: boolean
  in_production_flag: boolean
}

// ==================== Comment Types ====================

export type CommentType = 'GENERAL' | 'PROGRAMMING' | 'BIOSTAT' | 'QUESTION' | 'ISSUE' | 'RESPONSE'

export interface TrackerComment {
  id: number
  tracker_id: number
  user_id: number
  comment_text: string
  comment_type: CommentType
  is_resolved: boolean
  parent_comment_id?: number
  created_at: string
  updated_at: string
  user?: User
  replies?: TrackerComment[]
}

// ==================== Database Backup Types ====================

export interface DatabaseBackup {
  filename: string
  size: number
  created_at: string
  description?: string
}

// ==================== Audit Log Types ====================

export type AuditAction = 'CREATE' | 'UPDATE' | 'DELETE'

export interface AuditLog {
  id: number
  table_name: string
  record_id: number
  action: AuditAction
  user_id?: number
  user_name?: string
  user_email?: string
  changes_json?: string
  ip_address?: string
  user_agent?: string
  created_at: string
}

export interface AuditLogFilters {
  table_name?: string
  user_id?: number
  action?: AuditAction
  start_date?: string
  end_date?: string
  skip?: number
  limit?: number
}

export interface AuditLogSummary {
  by_action: Record<string, number>
  by_table: Record<string, number>
  by_user: Array<{ user_id: number; user_name: string; count: number }>
  by_day: Array<{ date: string; count: number }>
  total_count: number
}

// ==================== API Response Types ====================

export interface ApiError {
  detail: string
}

export interface BulkOperationResult {
  success: boolean
  created: number
  updated: number
  errors: string[]
}

// ==================== WebSocket Event Types ====================

export type WebSocketEventType = 
  | 'study_created' | 'study_updated' | 'study_deleted'
  | 'database_release_created' | 'database_release_updated' | 'database_release_deleted'
  | 'reporting_effort_created' | 'reporting_effort_updated' | 'reporting_effort_deleted'
  | 'package_created' | 'package_updated' | 'package_deleted'
  | 'package_item_created' | 'package_item_updated' | 'package_item_deleted'
  | 'reporting_effort_item_created' | 'reporting_effort_item_updated' | 'reporting_effort_item_deleted'
  | 'reporting_effort_tracker_created' | 'reporting_effort_tracker_updated' | 'reporting_effort_tracker_deleted'
  | 'comment_created' | 'comment_updated' | 'comment_resolved'
  | 'user_created' | 'user_updated' | 'user_deleted'
  | 'text_element_created' | 'text_element_updated' | 'text_element_deleted'
  | 'notification_created' | 'notification_count_updated'

export interface WebSocketMessage {
  type: WebSocketEventType
  data: Record<string, unknown>
  timestamp: string
}

// ==================== Application Settings Types ====================

export interface AppSettings {
  id: number
  default_due_date_offset: number
  updated_by_user_id?: number
  updated_by_username?: string
  created_at: string
  updated_at: string
}

export interface AppSettingsUpdate {
  default_due_date_offset?: number
}

// ==================== Form Types ====================

export interface StudyFormData {
  study_label: string
}

export interface BulkHierarchyRow {
  study_label: string
  database_release_label: string
  reporting_effort_label: string
}

export interface BulkHierarchyResponse {
  success: boolean
  created_studies: number
  created_releases: number
  created_efforts: number
  skipped_duplicates: number
  errors: string[]
}

export interface DatabaseReleaseFormData {
  study_id: number
  database_release_label: string
  database_release_date: string
}

export interface ReportingEffortFormData {
  study_id: number
  database_release_id: number
  database_release_label: string
}

export interface UserFormData {
  username: string
  email: string
  password?: string  // Optional for updates
  is_admin: boolean
  department?: string
  generatePassword?: boolean
}

export interface TextElementFormData {
  type: TextElementType
  label: string
  content?: string
}

export interface PackageFormData {
  package_name: string
  study_indication?: string
  therapeutic_area?: string
}

export interface TrackerFormData {
  reporting_effort_item_id: number
  production_programmer_id?: number
  qc_programmer_id?: number
  production_status: TrackerStatus
  qc_status: TrackerStatus
  priority?: Priority
  due_date?: string
  qc_completion_date?: string
}

// ==================== Milestone Tracking Types ====================

// Valid subtypes for milestone linking
export const MILESTONE_LINKABLE_SUBTYPES = ['Table', 'Listing', 'Figure', 'SDTM', 'ADaM'] as const
export type MilestoneLinkableSubtype = (typeof MILESTONE_LINKABLE_SUBTYPES)[number]

export interface ReportingEffortMilestone {
  id: number
  phase_id: number
  name: string
  start_date?: string
  due_date?: string
  responsibility?: string
  comments?: string
  is_completed: boolean
  completion_date?: string
  display_order: number
  // Tracker linking fields
  linked_subtype?: MilestoneLinkableSubtype
  linked_tag_id?: number
  created_at: string
  updated_at: string
}

export interface ReportingEffortMilestoneWithTrackers extends ReportingEffortMilestone {
  linked_tag_name?: string
  linked_tracker_ids: number[]
  linked_tracker_count: number
  trackers_past_due: number
}

export interface LinkedTrackerInfo {
  id: number
  item_code: string
  item_subtype: string
  due_date?: string
  link_type: MilestoneLinkType
  is_past_due: boolean
}

export interface ReportingEffortPhase {
  id: number
  reporting_effort_id: number
  name: string
  display_order: number
  created_at: string
  updated_at: string
  milestones?: ReportingEffortMilestone[]
}

export interface ReportingEffortMilestoneWithContext extends ReportingEffortMilestone {
  phase_name?: string
  reporting_effort_id?: number
  reporting_effort_label?: string
  study_id?: number
  study_label?: string
}

export interface MilestoneFormData {
  name: string
  start_date?: string
  due_date?: string
  responsibility?: string
  comments?: string
  is_completed?: boolean
  display_order?: number
  // Tracker linking fields
  linked_subtype?: MilestoneLinkableSubtype | null
  linked_tag_id?: number | null
  linked_tracker_ids?: number[]
}

export interface PhaseFormData {
  name: string
  display_order?: number
}

export interface MilestoneTrackerLinkingTag {
  id: number
  name: string
  color: string
}

