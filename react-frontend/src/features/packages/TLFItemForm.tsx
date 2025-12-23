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
import { TextElementCombobox } from '@/components/common/TextElementCombobox'

export interface TLFFormData {
  item_subtype: string // Table, Listing, Figure
  item_code: string // TLF ID like t14.1.1
  title_id?: number | null
  population_flag_id?: number | null
  ich_category_id?: number | null
  footnote_ids?: number[]
  acronym_ids?: number[]
}

interface TLFItemFormProps {
  data: TLFFormData
  onChange: (data: TLFFormData) => void
  disabled?: boolean
}

export function TLFItemForm({ data, onChange, disabled = false }: TLFItemFormProps) {
  const handleChange = (field: keyof TLFFormData, value: unknown) => {
    onChange({ ...data, [field]: value })
  }

  return (
    <div className="space-y-4">
      {/* Row 1: Type and Code */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="tlf-type">TLF Type *</Label>
          <Select
            value={data.item_subtype}
            onValueChange={(value) => handleChange('item_subtype', value)}
            disabled={disabled}
          >
            <SelectTrigger id="tlf-type">
              <SelectValue placeholder="Select type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Table">Table</SelectItem>
              <SelectItem value="Listing">Listing</SelectItem>
              <SelectItem value="Figure">Figure</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="tlf-code">Title Key / Code *</Label>
          <Input
            id="tlf-code"
            value={data.item_code}
            onChange={(e) => handleChange('item_code', e.target.value)}
            placeholder="e.g., t14.1.1"
            disabled={disabled}
          />
        </div>
      </div>

      {/* Row 2: Title */}
      <div className="space-y-2">
        <Label>Title</Label>
        <TextElementCombobox
          type="title"
          value={data.title_id}
          onChange={(id) => handleChange('title_id', id)}
          placeholder="Search or create title..."
          disabled={disabled}
        />
      </div>

      {/* Row 3: Population and ICH Category */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Population Flag</Label>
          <TextElementCombobox
            type="population_set"
            value={data.population_flag_id}
            onChange={(id) => handleChange('population_flag_id', id)}
            placeholder="Search or create population..."
            disabled={disabled}
          />
        </div>

        <div className="space-y-2">
          <Label>ICH Category</Label>
          <TextElementCombobox
            type="ich_category"
            value={data.ich_category_id}
            onChange={(id) => handleChange('ich_category_id', id)}
            placeholder="Search or create ICH category..."
            disabled={disabled}
          />
        </div>
      </div>

      {/* Row 4: Footnotes (multi-select) */}
      <div className="space-y-2">
        <Label>Footnotes</Label>
        <TextElementCombobox
          type="footnote"
          values={data.footnote_ids || []}
          onMultiChange={(ids) => handleChange('footnote_ids', ids)}
          multiple
          placeholder="Search or create footnotes..."
          disabled={disabled}
        />
      </div>

      {/* Row 5: Acronyms (multi-select) */}
      <div className="space-y-2">
        <Label>Acronyms</Label>
        <TextElementCombobox
          type="acronyms_set"
          values={data.acronym_ids || []}
          onMultiChange={(ids) => handleChange('acronym_ids', ids)}
          multiple
          placeholder="Search or create acronyms..."
          disabled={disabled}
        />
      </div>
    </div>
  )
}

