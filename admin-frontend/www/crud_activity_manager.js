// Universal CRUD Activity Manager for PEARL
// Handles all cross-browser CRUD updates with context-aware strategies

class UniversalCRUDManager {
    constructor() {
        // User context tracking
        this.userContext = {
            activeModal: null,          // {type: 'edit', entity: 'study', id: 123}
            activeForm: null,           // Currently focused form
            dirtyFields: new Set(),     // Form fields with unsaved changes
            activeTable: null,          // Current DataTable being viewed
            lastInteraction: Date.now(),
            isTyping: false,
            recentActivity: []          // Track recent user actions
        };
        
        // Update management
        this.updateQueue = [];          // Deferred updates
        this.conflictBuffer = [];       // Conflicts needing resolution
        this.processingUpdate = false;  // Prevent recursive updates
        
        // Strategy handlers
        this.strategies = {
            'APPLY_IMMEDIATELY': this.applyImmediately.bind(this),
            'APPLY_WITH_NOTIFICATION': this.applyWithNotification.bind(this),
            'QUEUE_FOR_IDLE': this.queueForIdle.bind(this),
            'QUEUE_FOR_MODAL_CLOSE': this.queueForModalClose.bind(this),
            'SHOW_CONFLICT_DIALOG': this.showConflictDialog.bind(this)
        };
        
        // Activity tracking timer
        this.idleTimer = null;
        this.IDLE_THRESHOLD = 10000; // 10 seconds
        
        // Initialize
        this.initializeActivityTracking();
        this.initializeEventListeners();
        
        console.log('🎯 Universal CRUD Manager initialized');
    }
    
    // =============================================================================
    // CORE CRUD EVENT HANDLING
    // =============================================================================
    
    /**
     * Main entry point for all CRUD events from WebSocket
     * @param {Object} event - WebSocket CRUD event
     */
    handleCRUDEvent(event) {
        if (this.processingUpdate) {
            console.log('⏳ Update in progress, queueing event:', event.type);
            this.updateQueue.push(event);
            return;
        }
        
        console.log('📨 Processing CRUD event:', event.type, event.entity?.type, event.entity?.id);
        
        // Determine strategy
        const strategy = this.determineStrategy(event);
        console.log('🎯 Strategy determined:', strategy);
        
        // Execute strategy
        this.executeStrategy(strategy, event);
    }
    
    /**
     * Determine the appropriate strategy for handling an update
     * @param {Object} event - CRUD event
     * @returns {string} Strategy name
     */
    determineStrategy(event) {
        // Check for direct conflicts first
        if (this.isDirectConflict(event)) {
            return 'SHOW_CONFLICT_DIALOG';
        }
        
        // Check if user is in a modal for different entity
        if (this.userContext.activeModal && !this.isRelatedEntity(event)) {
            return 'QUEUE_FOR_MODAL_CLOSE';
        }
        
        // Check if user is actively typing/working
        if (this.isUserActivelyWorking()) {
            // If it's the same entity they're working on, queue for idle
            if (this.isRelatedToActiveWork(event)) {
                return 'QUEUE_FOR_IDLE';
            }
            // If it's unrelated work, apply with notification
            return 'APPLY_WITH_NOTIFICATION';
        }
        
        // Check if it's a non-visible update (badges, counts, etc.)
        if (this.isNonVisibleUpdate(event)) {
            return 'APPLY_IMMEDIATELY';
        }
        
        // Default: safe to apply with notification
        return 'APPLY_WITH_NOTIFICATION';
    }
    
    /**
     * Execute the determined strategy
     * @param {string} strategy - Strategy name
     * @param {Object} event - CRUD event
     */
    executeStrategy(strategy, event) {
        if (!this.strategies[strategy]) {
            console.warn('⚠️ Unknown strategy:', strategy);
            this.strategies['APPLY_WITH_NOTIFICATION'](event);
            return;
        }
        
        this.strategies[strategy](event);
    }
    
    // =============================================================================
    // STRATEGY IMPLEMENTATIONS
    // =============================================================================
    
    /**
     * Apply update immediately (silent updates like badges)
     */
    applyImmediately(event) {
        console.log('⚡ Applying immediately:', event.type);
        this.processingUpdate = true;
        
        try {
            this.applyUpdate(event);
            this.showSubtleIndicator(event, 'applied');
        } catch (error) {
            console.error('❌ Error applying immediate update:', error);
        } finally {
            this.processingUpdate = false;
            this.processQueuedUpdates();
        }
    }
    
    /**
     * Apply update with user notification
     */
    applyWithNotification(event) {
        console.log('🔔 Applying with notification:', event.type);
        this.processingUpdate = true;
        
        try {
            this.applyUpdate(event);
            this.showNotification(event, 'info');
        } catch (error) {
            console.error('❌ Error applying update with notification:', error);
        } finally {
            this.processingUpdate = false;
            this.processQueuedUpdates();
        }
    }
    
    /**
     * Queue update for when user becomes idle
     */
    queueForIdle(event) {
        console.log('⏰ Queueing for idle:', event.type);
        this.updateQueue.push({
            ...event,
            strategy: 'APPLY_WITH_NOTIFICATION',
            queuedAt: Date.now(),
            reason: 'user_active'
        });
        
        this.showQueuedUpdateIndicator();
        this.resetIdleTimer();
    }
    
    /**
     * Queue update for when modal closes
     */
    queueForModalClose(event) {
        console.log('📋 Queueing for modal close:', event.type);
        this.updateQueue.push({
            ...event,
            strategy: 'APPLY_WITH_NOTIFICATION',
            queuedAt: Date.now(),
            reason: 'modal_open'
        });
        
        this.showQueuedUpdateIndicator();
    }
    
    /**
     * Show conflict resolution dialog
     */
    showConflictDialog(event) {
        console.log('⚔️ Showing conflict dialog:', event.type);
        
        this.conflictBuffer.push(event);
        this.displayConflictDialog(event);
    }
    
    // =============================================================================
    // USER CONTEXT DETECTION
    // =============================================================================
    
    /**
     * Check if user is actively working
     */
    isUserActivelyWorking() {
        // Check if typing recently (within 5 seconds)
        const timeSinceActivity = Date.now() - this.userContext.lastInteraction;
        if (timeSinceActivity < 5000) {
            console.log('⚡ Recent activity detected:', timeSinceActivity, 'ms ago');
            return true;
        }
        
        // Check if any form elements are focused
        const activeElement = document.activeElement;
        if (activeElement && this.isFormElement(activeElement)) {
            console.log('🖊️ User is typing in:', activeElement.tagName, activeElement.id);
            return true;
        }
        
        // Check if any modals are open
        if (this.userContext.activeModal) {
            console.log('📋 User has modal open:', this.userContext.activeModal.type);
            return true;
        }
        
        // Check for open dialogs/modals in DOM
        const openModals = document.querySelectorAll('.modal.show, .swal2-container, [role="dialog"]:not([hidden])');
        if (openModals.length > 0) {
            console.log('📋 DOM modals detected:', openModals.length);
            return true;
        }
        
        return false;
    }
    
    /**
     * Check if event is a direct conflict with user's current work
     */
    isDirectConflict(event) {
        if (!this.userContext.activeModal) return false;
        
        const modal = this.userContext.activeModal;
        return (
            modal.entity === event.entity?.type &&
            modal.id === event.entity?.id &&
            (modal.type === 'edit' || modal.type === 'create') &&
            event.operation === 'update'
        );
    }
    
    /**
     * Check if event is related to user's active work
     */
    isRelatedToActiveWork(event) {
        if (!this.userContext.activeModal) return false;
        
        const modal = this.userContext.activeModal;
        return (
            modal.entity === event.entity?.type ||
            this.isParentChildRelationship(modal, event)
        );
    }
    
    /**
     * Check if event is related to current entity
     */
    isRelatedEntity(event) {
        if (!this.userContext.activeModal) return false;
        
        const modal = this.userContext.activeModal;
        return modal.entity === event.entity?.type;
    }
    
    /**
     * Check if update only affects non-visible elements
     */
    isNonVisibleUpdate(event) {
        const nonVisibleTypes = [
            'badge_update',
            'count_update',
            'status_update',
            'comment_count'
        ];
        
        return nonVisibleTypes.some(type => event.type.includes(type));
    }
    
    /**
     * Check if element is a form element
     */
    isFormElement(element) {
        const formTags = ['INPUT', 'TEXTAREA', 'SELECT'];
        return (
            formTags.includes(element.tagName) ||
            element.contentEditable === 'true'
        );
    }
    
    /**
     * Check parent-child relationships between entities
     */
    isParentChildRelationship(modal, event) {
        // Define entity relationships
        const relationships = {
            'study': ['database_release', 'reporting_effort'],
            'database_release': ['reporting_effort'],
            'reporting_effort': ['reporting_effort_item', 'tracker'],
            'reporting_effort_item': ['tracker'],
            'tracker': ['comment'],
            'package': ['package_item']
        };
        
        const modalEntity = modal.entity;
        const eventEntity = event.entity?.type;
        
        return (
            relationships[modalEntity]?.includes(eventEntity) ||
            relationships[eventEntity]?.includes(modalEntity)
        );
    }
    
    // =============================================================================
    // ACTIVITY TRACKING
    // =============================================================================
    
    /**
     * Initialize activity tracking
     */
    initializeActivityTracking() {
        // Track user interactions
        const events = ['keydown', 'mousedown', 'focus', 'input', 'change'];
        events.forEach(event => {
            document.addEventListener(event, this.onUserActivity.bind(this), true);
        });
        
        // Track form changes
        document.addEventListener('input', this.onFormChange.bind(this), true);
        document.addEventListener('change', this.onFormChange.bind(this), true);
    }
    
    /**
     * Handle user activity
     */
    onUserActivity(event) {
        this.userContext.lastInteraction = Date.now();
        this.userContext.recentActivity.push({
            type: event.type,
            target: event.target.tagName,
            timestamp: Date.now()
        });
        
        // Keep only last 10 activities
        if (this.userContext.recentActivity.length > 10) {
            this.userContext.recentActivity.shift();
        }
        
        this.resetIdleTimer();
    }
    
    /**
     * Handle form changes (dirty tracking)
     */
    onFormChange(event) {
        if (this.isFormElement(event.target)) {
            const fieldId = event.target.id || event.target.name;
            if (fieldId) {
                this.userContext.dirtyFields.add(fieldId);
                console.log('📝 Form field changed:', fieldId);
            }
        }
    }
    
    /**
     * Reset idle timer
     */
    resetIdleTimer() {
        if (this.idleTimer) {
            clearTimeout(this.idleTimer);
        }
        
        this.idleTimer = setTimeout(() => {
            this.onUserIdle();
        }, this.IDLE_THRESHOLD);
    }
    
    /**
     * Handle user becoming idle
     */
    onUserIdle() {
        console.log('😴 User idle detected - processing queued updates');
        this.processQueuedUpdates();
    }
    
    // =============================================================================
    // UPDATE PROCESSING
    // =============================================================================
    
    /**
     * Apply an update to the UI
     */
    applyUpdate(event) {
        console.log('🔄 Applying update:', event.type, event.entity);
        
        // Route to appropriate handler based on event type
        if (event.operation === 'create') {
            this.handleCreateUpdate(event);
        } else if (event.operation === 'update') {
            this.handleUpdateEvent(event);
        } else if (event.operation === 'delete') {
            this.handleDeleteUpdate(event);
        } else {
            // Legacy event types
            this.handleLegacyEvent(event);
        }
    }
    
    /**
     * Handle create operations
     */
    handleCreateUpdate(event) {
        console.log('➕ Handling create update:', event.entity?.type);
        
        // Trigger Shiny refresh for the relevant module
        this.triggerShinyRefresh(event.entity?.type);
        
        // Add visual feedback
        this.addCreateAnimation(event);
    }
    
    /**
     * Handle update operations
     */
    handleUpdateEvent(event) {
        console.log('✏️ Handling update event:', event.entity?.type);
        
        // Trigger Shiny refresh for the relevant module
        this.triggerShinyRefresh(event.entity?.type);
        
        // Add visual feedback
        this.addUpdateAnimation(event);
    }
    
    /**
     * Handle delete operations
     */
    handleDeleteUpdate(event) {
        console.log('🗑️ Handling delete update:', event.entity?.type);
        
        // Try surgical removal first
        const surgicalSuccess = this.attemptSurgicalRemoval(event);
        
        if (!surgicalSuccess) {
            // Fall back to full refresh
            this.triggerShinyRefresh(event.entity?.type);
        }
        
        // Add visual feedback
        this.addDeleteAnimation(event);
    }
    
    /**
     * Handle legacy event formats
     */
    handleLegacyEvent(event) {
        console.log('🔄 Handling legacy event:', event.type);
        
        // Send to Shiny as before for backward compatibility
        if (typeof Shiny !== 'undefined' && Shiny.setInputValue) {
            Shiny.setInputValue('universal_crud_event', {
                type: event.type,
                data: event.data || event.entity?.data,
                timestamp: Date.now()
            }, {priority: 'event'});
        } else {
            console.log('⚠️ Shiny.setInputValue not available yet - legacy event deferred:', event.type);
        }
    }
    
    /**
     * Trigger Shiny module refresh
     */
    triggerShinyRefresh(entityType) {
        if (typeof Shiny === 'undefined' || !Shiny.setInputValue) {
            console.log('⚠️ Shiny.setInputValue not available yet - refresh deferred for:', entityType);
            return;
        }
        
        // Map entity types to module names (must match app.R module IDs)
        const moduleMap = {
            'study': 'study_tree',  // maps to study_tree module in app.R
            'database_release': 'study_tree',  // database releases are handled by study_tree module
            'reporting_effort': 'study_tree',  // reporting efforts are handled by study_tree module
            'reporting_effort_item': 'reporting_effort_items',
            'tracker': 'reporting_effort_tracker',
            'comment': 'reporting_effort_tracker',
            'text_element': 'tnfp',
            'package': 'packages_simple',  // Fixed: should match app.R module ID "packages_simple"
            'package_item': 'package_items',
            'user': 'users'
        };
        
        const moduleName = moduleMap[entityType];
        if (moduleName) {
            const inputId = `${moduleName}-crud_refresh`;
            // Use a random value to ensure Shiny always sees this as a change
            const refreshValue = Math.random() + Date.now();
            console.log('📤 Triggering Shiny refresh:', inputId, 'with value:', refreshValue);
            Shiny.setInputValue(inputId, refreshValue, {priority: 'event'});
        }
    }
    
    /**
     * Process queued updates
     */
    processQueuedUpdates() {
        if (this.updateQueue.length === 0) return;
        
        console.log(`🔄 Processing ${this.updateQueue.length} queued updates`);
        
        const updates = [...this.updateQueue];
        this.updateQueue = [];
        
        updates.forEach(update => {
            // Re-check strategy in case context changed
            const strategy = update.strategy || this.determineStrategy(update);
            this.executeStrategy(strategy, update);
        });
        
        this.hideQueuedUpdateIndicator();
    }
    
    // =============================================================================
    // PUBLIC API
    // =============================================================================
    
    /**
     * Set active modal context
     */
    setActiveModal(modalInfo) {
        this.userContext.activeModal = modalInfo;
        console.log('📋 Active modal set:', modalInfo);
    }
    
    /**
     * Clear active modal context
     */
    clearActiveModal() {
        this.userContext.activeModal = null;
        this.userContext.dirtyFields.clear();
        console.log('📋 Active modal cleared');
        
        // Process any queued updates waiting for modal close
        setTimeout(() => this.processQueuedUpdates(), 100);
    }
    
    /**
     * Get current user context
     */
    getUserContext() {
        return { ...this.userContext };
    }
    
    /**
     * Get queued updates count
     */
    getQueuedUpdatesCount() {
        return this.updateQueue.length;
    }
    
    /**
     * Manually apply queued updates
     */
    applyQueuedUpdates() {
        this.processQueuedUpdates();
    }
    
    // =============================================================================
    // PLACEHOLDER METHODS (TO BE IMPLEMENTED IN LATER PHASES)
    // =============================================================================
    
    initializeEventListeners() {
        // Will be implemented in Phase 2
        console.log('🔗 Event listeners initialized (placeholder)');
    }
    
    attemptSurgicalRemoval(event) {
        // Will be implemented in Phase 2
        console.log('✂️ Surgical removal attempted (placeholder)');
        return false;
    }
    
    addCreateAnimation(event) {
        console.log('✨ Create animation (placeholder)');
    }
    
    addUpdateAnimation(event) {
        console.log('✨ Update animation (placeholder)');
    }
    
    addDeleteAnimation(event) {
        console.log('✨ Delete animation (placeholder)');
    }
    
    showNotification(event, type) {
        console.log('🔔 Notification (placeholder):', type, event.type);
    }
    
    showSubtleIndicator(event, status) {
        console.log('💫 Subtle indicator (placeholder):', status);
    }
    
    showQueuedUpdateIndicator() {
        console.log('📊 Queued update indicator shown (placeholder)');
    }
    
    hideQueuedUpdateIndicator() {
        console.log('📊 Queued update indicator hidden (placeholder)');
    }
    
    displayConflictDialog(event) {
        console.log('⚔️ Conflict dialog (placeholder)');
    }
}

// =============================================================================
// GLOBAL INITIALIZATION
// =============================================================================

// Create global instance
window.crudManager = null;

/**
 * Initialize the Universal CRUD Manager
 */
function initializeCRUDManager() {
    if (window.crudManager) {
        console.log('⚠️ CRUD Manager already initialized');
        return;
    }
    
    console.log('🚀 Initializing Universal CRUD Manager');
    window.crudManager = new UniversalCRUDManager();
    
    // Add to window for debugging
    window.pearlCRUD = {
        manager: window.crudManager,
        getUserContext: () => window.crudManager.getUserContext(),
        getQueuedCount: () => window.crudManager.getQueuedUpdatesCount(),
        applyQueued: () => window.crudManager.applyQueuedUpdates(),
        setModal: (modalInfo) => window.crudManager.setActiveModal(modalInfo),
        clearModal: () => window.crudManager.clearActiveModal()
    };
    
    console.log('✅ Universal CRUD Manager ready');
    console.log('💡 Debug: window.pearlCRUD available for testing');
}

// Initialize IMMEDIATELY when script loads to ensure it's available for WebSocket messages
// This prevents race conditions where WebSocket messages arrive before DOMContentLoaded
initializeCRUDManager();

// Also set up DOM-dependent features when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        console.log('📄 DOM ready - CRUD Manager already initialized');
    });
}

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (window.crudManager && window.crudManager.idleTimer) {
        clearTimeout(window.crudManager.idleTimer);
    }
});

console.log('📁 Universal CRUD Activity Manager loaded');