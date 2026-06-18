<template>
  <div class="mindmap-wrap">
    <svg :viewBox="viewBox" class="mindmap" role="img" aria-label="知识关系图谱">
      <g v-for="edge in edges" :key="edge.id">
        <path :d="edge.d" class="edge" />
      </g>

      <g v-for="node in nodes" :key="node.id" :transform="`translate(${node.x}, ${node.y})`">
        <rect :width="node.w" :height="node.h" rx="8" :class="['node-rect', node.kind]" />
        <text :x="node.w / 2" :y="node.textY" text-anchor="middle" class="node-text">
          <tspan
            v-for="(line, index) in node.lines"
            :key="`${node.id}-${index}`"
            :x="node.w / 2"
            :dy="index === 0 ? 0 : 15"
          >
            {{ line }}
          </tspan>
        </text>
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ProfileJson } from '@/api/profile'

const props = defineProps<{
  profile: ProfileJson
}>()

const mainFocus = computed(() => {
  return props.profile.llm_profile?.main_focus || props.profile.overview?.main_focus || '知识画像'
})

const clusterData = computed(() => {
  const llmClusters = props.profile.llm_profile?.knowledge_clusters || []
  if (llmClusters.length > 0) {
    return llmClusters.slice(0, 8).map((c) => ({
      name: c.cluster,
      keywords: c.related_keywords || [],
    }))
  }

  return (props.profile.knowledge_clusters || []).slice(0, 8).map((c) => ({
    name: c.cluster,
    keywords: c.related_items || [],
  }))
})

const nodes = computed(() => {
  const result: Array<{
    id: string
    label: string
    x: number
    y: number
    w: number
    h: number
    kind: string
    lines: string[]
    textY: number
  }> = []

  result.push({
    id: 'center',
    label: shortText(mainFocus.value, 22),
    x: -110,
    y: -38,
    w: 220,
    h: 76,
    kind: 'center',
    lines: wrapText(mainFocus.value, 11, 2),
    textY: 34,
  })

  const count = Math.max(1, clusterData.value.length)
  clusterData.value.forEach((cluster, i) => {
    const angle = -Math.PI / 2 + i * 2 * Math.PI / count
    const cx = 300 * Math.cos(angle)
    const cy = 245 * Math.sin(angle)
    result.push({
      id: `cluster-${i}`,
      label: shortText(cluster.name, 20),
      x: cx - 92,
      y: cy - 30,
      w: 184,
      h: 60,
      kind: 'cluster',
      lines: wrapText(cluster.name, 10, 2),
      textY: 27,
    })

    cluster.keywords.slice(0, 4).forEach((keyword, j) => {
      const subAngle = angle + (j - 1.5) * 0.28
      const tx = cx + 142 * Math.cos(subAngle)
      const ty = cy + 142 * Math.sin(subAngle)
      result.push({
        id: `tag-${i}-${j}`,
        label: shortText(String(keyword), 12),
        x: tx - 58,
        y: ty - 19,
        w: 116,
        h: 38,
        kind: 'tag',
        lines: wrapText(String(keyword), 6, 2),
        textY: 18,
      })
    })
  })

  return result
})

const viewBox = computed(() => {
  if (nodes.value.length === 0) return '-520 -400 1040 800'

  const padding = 90
  const minX = Math.min(...nodes.value.map((node) => node.x)) - padding
  const minY = Math.min(...nodes.value.map((node) => node.y)) - padding
  const maxX = Math.max(...nodes.value.map((node) => node.x + node.w)) + padding
  const maxY = Math.max(...nodes.value.map((node) => node.y + node.h)) + padding

  return `${minX} ${minY} ${maxX - minX} ${maxY - minY}`
})

const edges = computed(() => {
  const result: Array<{ id: string; d: string }> = []

  nodes.value.filter((node) => node.id.startsWith('cluster-')).forEach((node) => {
    const x = node.x + node.w / 2
    const y = node.y + node.h / 2
    result.push({
      id: `e-${node.id}`,
      d: `M 0 0 C ${x * 0.35} 0, ${x * 0.65} ${y}, ${x} ${y}`,
    })
  })

  nodes.value.filter((node) => node.id.startsWith('tag-')).forEach((node) => {
    const [, clusterIndex] = node.id.split('-')
    const parent = nodes.value.find((n) => n.id === `cluster-${clusterIndex}`)
    if (!parent) return

    const x1 = parent.x + parent.w / 2
    const y1 = parent.y + parent.h / 2
    const x2 = node.x + node.w / 2
    const y2 = node.y + node.h / 2
    result.push({
      id: `e-${node.id}`,
      d: `M ${x1} ${y1} C ${(x1 + x2) / 2} ${y1}, ${(x1 + x2) / 2} ${y2}, ${x2} ${y2}`,
    })
  })

  return result
})

function shortText(text = '', max = 12): string {
  return text.length > max ? `${text.slice(0, max)}...` : text
}

function wrapText(text = '', maxPerLine = 8, maxLines = 2): string[] {
  const source = text.trim()
  if (!source) return ['-']

  const lines: string[] = []
  for (let i = 0; i < source.length && lines.length < maxLines; i += maxPerLine) {
    lines.push(source.slice(i, i + maxPerLine))
  }

  if (source.length > maxPerLine * maxLines) {
    const last = lines.length - 1
    lines[last] = `${lines[last].slice(0, Math.max(1, maxPerLine - 3))}...`
  }

  return lines
}
</script>

<style scoped>
.mindmap-wrap {
  width: 100%;
  height: clamp(520px, 62vh, 760px);
  border-radius: 8px;
  background: radial-gradient(circle at center, #10213a 0%, #0d1117 72%);
  overflow: visible;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.mindmap {
  width: 100%;
  height: 100%;
}

.edge {
  fill: none;
  stroke: #2563eb;
  stroke-width: 1.6;
  opacity: 0.58;
}

.node-rect {
  stroke-width: 1.5;
  filter: drop-shadow(0 0 6px rgba(37, 99, 235, 0.18));
}

.node-rect.center {
  fill: #1d4ed8;
  stroke: #38bdf8;
}

.node-rect.cluster {
  fill: #0f3b69;
  stroke: #60a5fa;
}

.node-rect.tag {
  fill: #172033;
  stroke: #334155;
}

.node-text {
  fill: #e5edf7;
  font-size: 11px;
  font-weight: 700;
  pointer-events: none;
}
</style>
