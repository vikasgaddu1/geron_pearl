import { useMemo } from 'react'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useIGVersions } from '@/api'

export interface DatasetFormData {
  item_subtype: string // SDTM or ADaM
  item_code: string // Dataset name like DM, AE, ADSL
  label?: string
  sorting_order?: number
  ig_version_id?: number
}

interface DatasetItemFormProps {
  data: DatasetFormData
  onChange: (data: DatasetFormData) => void
  disabled?: boolean
}

export function DatasetItemForm({ data, onChange, disabled = false }: DatasetItemFormProps) {
  // Fetch IG versions
  const { data: igVersions = [] } = useIGVersions({ active_only: true })

  const handleChange = (field: keyof DatasetFormData, value: unknown) => {
    onChange({ ...data, [field]: value })
  }

  // Filter IG versions based on dataset type
  const filteredIGVersions = useMemo(() => {
    const standardType = data.item_subtype === 'SDTM' ? 'SDTM' : 'ADaM'
    return igVersions.filter(v => v.standard_type === standardType)
  }, [igVersions, data.item_subtype])

  // Get latest IG version for each standard type (for default selection)
  const latestIGVersions = useMemo(() => {
    const getLatestVersion = (standardType: 'SDTM' | 'ADaM') => {
      const versions = igVersions.filter(v => v.standard_type === standardType)
      if (versions.length === 0) return undefined
      return versions.sort((a, b) => {
        const [aMajor, aMinor] = a.version.split('.').map(Number)
        const [bMajor, bMinor] = b.version.split('.').map(Number)
        if (bMajor !== aMajor) return bMajor - aMajor
        return (bMinor || 0) - (aMinor || 0)
      })[0]
    }
    return {
      SDTM: getLatestVersion('SDTM'),
      ADaM: getLatestVersion('ADaM'),
    }
  }, [igVersions])

  const handleSubtypeChange = (value: string) => {
    // Auto-select latest IG version when switching between SDTM and ADaM
    const newIGVersionId = value === 'SDTM' ? latestIGVersions.SDTM?.id : latestIGVersions.ADaM?.id
    onChange({ ...data, item_subtype: value, ig_version_id: newIGVersionId })
  }

  return (
    <div className="space-y-4">
      {/* Row 1: Type and Name */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="dataset-type">Dataset Type *</Label>
          <Select
            value={data.item_subtype}
            onValueChange={handleSubtypeChange}
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
        <p className="text-xs text-muted-foreground">
          Descriptive name for the dataset (shown in dashboards)
        </p>
      </div>

      {/* Row 3: IG Version */}
      {filteredIGVersions.length > 0 && (
        <div className="space-y-2">
          <Label htmlFor="ig-version">IG Version</Label>
          <Select
            value={data.ig_version_id?.toString() || '__none__'}
            onValueChange={(value) => handleChange('ig_version_id', value === '__none__' ? undefined : parseInt(value))}
            disabled={disabled}
          >
            <SelectTrigger id="ig-version">
              <SelectValue placeholder="Select IG version" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__none__">None</SelectItem>
              {filteredIGVersions.map((version) => (
                <SelectItem key={version.id} value={String(version.id)}>
                  v{version.version} {version.description && `- ${version.description}`}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            {data.item_subtype} Implementation Guide version
          </p>
        </div>
      )}

      {/* Row 4: Run Order */}
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
        <p className="text-xs text-muted-foreground">
          Order in which dataset programs should be run
        </p>
      </div>
    </div>
  )
}










