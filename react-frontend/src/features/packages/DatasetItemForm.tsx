import React from 'react'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export interface DatasetFormData {
  item_subtype: string // SDTM or ADaM
  item_code: string // Dataset name like DM, AE, ADSL
  label?: string
  sorting_order?: number
}

interface DatasetItemFormProps {
  data: DatasetFormData
  onChange: (data: DatasetFormData) => void
  disabled?: boolean
}

export function DatasetItemForm({ data, onChange, disabled = false }: DatasetItemFormProps) {
  const handleChange = (field: keyof DatasetFormData, value: unknown) => {
    onChange({ ...data, [field]: value })
  }

  return (
    <div className="space-y-4">
      {/* Row 1: Type and Name */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="dataset-type">Dataset Type *</Label>
          <Select
            value={data.item_subtype}
            onValueChange={(value) => handleChange('item_subtype', value)}
            disabled={disabled}
          >
            <SelectTrigger id="dataset-type">
              <SelectValue placeholder="Select type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="SDTM">SDTM</SelectItem>
              <SelectItem value="ADaM">ADaM</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="dataset-name">Dataset Name *</Label>
          <Input
            id="dataset-name"
            value={data.item_code}
            onChange={(e) => handleChange('item_code', e.target.value.toUpperCase())}
            placeholder="e.g., DM, AE, ADSL"
            disabled={disabled}
          />
        </div>
      </div>

      {/* Row 2: Label */}
      <div className="space-y-2">
        <Label htmlFor="dataset-label">Dataset Label</Label>
        <Input
          id="dataset-label"
          value={data.label || ''}
          onChange={(e) => handleChange('label', e.target.value)}
          placeholder="e.g., Demographics, Adverse Events"
          disabled={disabled}
        />
      </div>

      {/* Row 3: Run Order */}
      <div className="space-y-2">
        <Label htmlFor="sorting-order">Run Order</Label>
        <Input
          id="sorting-order"
          type="number"
          min={1}
          value={data.sorting_order || ''}
          onChange={(e) => handleChange('sorting_order', e.target.value ? parseInt(e.target.value) : undefined)}
          placeholder="Display order (1, 2, 3...)"
          disabled={disabled}
        />
      </div>
    </div>
  )
}

