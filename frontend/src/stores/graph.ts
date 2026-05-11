import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { KnowledgeNode, KnowledgeLink, Hyperedge } from '@/types/graph'

export const useGraphStore = defineStore('graph', () => {
  const nodes = ref<KnowledgeNode[]>([])
  const links = ref<KnowledgeLink[]>([])
  const hyperedges = ref<Hyperedge[]>([])
  const selectedNode = ref<KnowledgeNode | null>(null)
  const highlightedNodeId = ref<string | null>(null)
  const glowNodeId = ref<string | null>(null)
  const autoRotate = ref(true)
  const cameraResetTrigger = ref(0)
  const isLoading = ref(false)

  const nodeById = computed(() => {
    const map = new Map<string, KnowledgeNode>()
    for (const n of nodes.value) map.set(n.id, n)
    return map
  })

  const communities = computed(() => {
    const map = new Map<number, KnowledgeNode[]>()
    for (const n of nodes.value) {
      if (n.community_id != null) {
        ;(map.get(n.community_id) ?? (map.set(n.community_id, []), map.get(n.community_id)!)).push(n)
      }
    }
    return map
  })

  function setGraphData(data: { nodes: KnowledgeNode[]; edges: KnowledgeLink[]; hyperedges: Hyperedge[] }) {
    nodes.value = data.nodes
    links.value = data.edges
    hyperedges.value = data.hyperedges
  }

  function setNodes(list: KnowledgeNode[]) {
    nodes.value = list
  }

  function setLinks(list: KnowledgeLink[]) {
    links.value = list
  }

  function setHyperedges(list: Hyperedge[]) {
    hyperedges.value = list
  }

  function selectNode(node: KnowledgeNode | null) {
    selectedNode.value = node
  }

  function highlightNode(nodeId: string) {
    highlightedNodeId.value = nodeId
    setTimeout(() => {
      highlightedNodeId.value = null
    }, 2000)
  }

  function glowNode(nodeId: string) {
    glowNodeId.value = nodeId
    setTimeout(() => {
      glowNodeId.value = null
    }, 4000)
  }

  function toggleAutoRotate() {
    autoRotate.value = !autoRotate.value
  }

  function resetCamera() {
    cameraResetTrigger.value++
  }

  return {
    nodes,
    links,
    hyperedges,
    selectedNode,
    highlightedNodeId,
    glowNodeId,
    autoRotate,
    cameraResetTrigger,
    isLoading,
    nodeById,
    communities,
    setGraphData,
    setNodes,
    setLinks,
    setHyperedges,
    selectNode,
    highlightNode,
    glowNode,
    toggleAutoRotate,
    resetCamera,
  }
})
