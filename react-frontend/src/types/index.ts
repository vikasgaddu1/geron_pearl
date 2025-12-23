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

export interface ReportingEffort {
  id: number
  database_release_id: number
  database_release_label: string
  created_at: string
  updated_at: string
}

export interface User {
  id: number
  username: string
  email?: string
  role: 'ADMIN' | 'EDITOR' | 'VIEWER'
  department?: string
  auth_provider?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// ==================== Text Element Types ====================

export type TextElementType = 'title' | 'footnote' | 'population_set' | 'acronyms_set' | 'ich_category'

export interface TextElement {
  id: number
  type: TextElementType
  label: string
  created_at: string
  updated_at: string
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
}

export interface DatasetDetails {
  id?: number
  package_item_id?: number
  label?: string
  sorting_order?: number
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
  item_status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED'
  created_at: string
  updated_at: string
}

// ==================== Tracker Types ====================

export type TrackerStatus = 'not_started' | 'in_progress' | 'completed' | 'on_hold' | 'failed'
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

export interface ReportingEffortItemTracker {
  id: number
  reporting_effort_item_id: number
  production_programmer_id?: number
  qc_programmer_id?: number
  production_status: TrackerStatus
  qc_status: TrackerStatus
  priority?: Priority
  due_date?: string
  qc_completion_date?: string
  created_at: string
  updated_at: string
  // Expanded fields
  item_code?: string
  item_description?: string
  item_title?: string
  item_type?: ItemType
  item_subtype?: ItemSubtype
  production_programmer?: User
  qc_programmer?: User
  comment_count?: number
  unresolved_comment_count?: number
  tags?: TrackerTagSummary[]
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

export interface WebSocketMessage {
  type: WebSocketEventType
  data: Record<string, unknown>
  timestamp: string
}

// ==================== Form Types ====================

export interface StudyFormData {
  study_label: string
}

export interface DatabaseReleaseFormData {
  study_id: number
  database_release_label: string
  database_release_date: string
}

export interface ReportingEffortFormData {
  database_release_id: number
  database_release_label: string
}

export interface UserFormData {
  username: string
  email: string
  password?: string  // Optional for updates
  role: User['role']
  department?: string
  generatePassword?: boolean
}

export interface TextElementFormData {
  type: TextElementType
  label: string
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


