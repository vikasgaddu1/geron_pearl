/**
 * Hook for managing CRUD dialog state and mutations
 * Reduces boilerplate in CRUD management components
 */
import { useState, useCallback } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { getErrorMessage } from '@/lib/utils'

interface CRUDDialogOptions<T, TFormData> {
  /** Query key for invalidation (e.g., ['packages']) */
  queryKey: string[]
  /** Entity name for toast messages (e.g., 'Package') */
  entityName: string
  /** API create function */
  createFn: (data: TFormData) => Promise<T>
  /** API update function */
  updateFn: (id: number, data: TFormData) => Promise<T>
  /** API delete function */
  deleteFn: (id: number) => Promise<void>
  /** Initial form data */
  initialFormData: TFormData
  /** Transform entity to form data (for edit) */
  entityToFormData: (entity: T) => TFormData
  /** Get entity ID */
  getEntityId: (entity: T) => number
  /** Optional callback after successful create */
  onCreateSuccess?: (entity: T) => void
  /** Optional callback after successful update */
  onUpdateSuccess?: (entity: T) => void
  /** Optional callback after successful delete */
  onDeleteSuccess?: () => void
}

export function useCRUDDialog<T, TFormData>({
  queryKey,
  entityName,
  createFn,
  updateFn,
  deleteFn,
  initialFormData,
  entityToFormData,
  getEntityId,
  onCreateSuccess,
  onUpdateSuccess,
  onDeleteSuccess,
}: CRUDDialogOptions<T, TFormData>) {
  const queryClient = useQueryClient()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedEntity, setSelectedEntity] = useState<T | null>(null)
  const [formData, setFormData] = useState<TFormData>(initialFormData)

  const invalidateQueries = useCallback(() => {
    queryClient.invalidateQueries({ queryKey })
  }, [queryClient, queryKey])

  // Create mutation
  const createMutation = useMutation({
    mutationFn: createFn,
    onSuccess: (entity) => {
      toast.success(`${entityName} created successfully`)
      invalidateQueries()
      setDialogOpen(false)
      resetForm()
      onCreateSuccess?.(entity)
    },
    onError: (error) => toast.error(`Failed to create ${entityName.toLowerCase()}: ${getErrorMessage(error)}`),
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: TFormData }) => updateFn(id, data),
    onSuccess: (entity) => {
      toast.success(`${entityName} updated successfully`)
      invalidateQueries()
      setDialogOpen(false)
      resetForm()
      onUpdateSuccess?.(entity)
    },
    onError: (error) => toast.error(`Failed to update ${entityName.toLowerCase()}: ${getErrorMessage(error)}`),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteFn,
    onSuccess: () => {
      toast.success(`${entityName} deleted successfully`)
      invalidateQueries()
      setSelectedEntity(null)
      setDeleteDialogOpen(false)
      onDeleteSuccess?.()
    },
    onError: (error) => toast.error(`Failed to delete ${entityName.toLowerCase()}: ${getErrorMessage(error)}`),
  })

  const resetForm = useCallback(() => {
    setFormData(initialFormData)
    setSelectedEntity(null)
  }, [initialFormData])

  const handleAdd = useCallback(() => {
    resetForm()
    setDialogOpen(true)
  }, [resetForm])

  const handleEdit = useCallback((entity: T) => {
    setSelectedEntity(entity)
    setFormData(entityToFormData(entity))
    setDialogOpen(true)
  }, [entityToFormData])

  const handleDelete = useCallback((entity: T) => {
    setSelectedEntity(entity)
    setDeleteDialogOpen(true)
  }, [])

  const handleSubmit = useCallback(() => {
    if (selectedEntity) {
      updateMutation.mutate({ id: getEntityId(selectedEntity), data: formData })
    } else {
      createMutation.mutate(formData)
    }
  }, [selectedEntity, formData, createMutation, updateMutation, getEntityId])

  const confirmDelete = useCallback(() => {
    if (selectedEntity) {
      deleteMutation.mutate(getEntityId(selectedEntity))
    }
  }, [selectedEntity, deleteMutation, getEntityId])

  return {
    // State
    dialogOpen,
    setDialogOpen,
    deleteDialogOpen,
    setDeleteDialogOpen,
    selectedEntity,
    setSelectedEntity,
    formData,
    setFormData,
    // Mutations
    createMutation,
    updateMutation,
    deleteMutation,
    // Handlers
    handleAdd,
    handleEdit,
    handleDelete,
    handleSubmit,
    confirmDelete,
    resetForm,
    // Loading states
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isSubmitting: createMutation.isPending || updateMutation.isPending,
  }
}
