import { ref, watch, type Ref, onBeforeUnmount } from 'vue'
import ForceGraph3D from '3d-force-graph'
import * as THREE from 'three'
import { useGraphStore } from '@/stores/graph'
import type { KnowledgeNode } from '@/types/graph'

// Type for the 3D Force Graph instance - use any to avoid complex type issues
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ForceGraphInstance = any

// Extended node type with 3d-force-graph properties
interface GraphNode extends KnowledgeNode {
  collapsed?: boolean
  val?: number
  x?: number
  y?: number
  z?: number
  vx?: number
  vy?: number
  vz?: number
  fx?: number | null
  fy?: number | null
  fz?: number | null
}

// Extended link type with 3d-force-graph properties
interface GraphLink {
  id: number
  source: string | GraphNode
  target: string | GraphNode
  relationship: string
  confidence: string
  confidence_score: number
  weight: number
}

export function useForceGraph(containerRef: Ref<HTMLElement | null>) {
  const graphStore = useGraphStore()
  const graphInstance = ref<ForceGraphInstance | null>(null)
  const isInitialized = ref(false)
  
  // State for interactions
  const highlightedNodeId = ref<string | null>(null)
  const collapsedNodes = ref<Set<string>>(new Set())
  const hoveredNodeId = ref<string | null>(null)
  const showNodeLabels = ref(true) // 控制是否显示节点名称
  const glowPhase = ref(0) // 0 = not glowing, 1-6 = glow animation frames
  
  // Track all links for collapse/expand functionality
  const allLinks = ref<GraphLink[]>([])
  const allNodes = ref<GraphNode[]>([])
  
  // Store node labels for visibility toggling
  const nodeLabelSprites = new Map<string, THREE.Sprite>()

  function createTextSprite(text: string, color: string): THREE.Sprite {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')!
    canvas.width = 256
    canvas.height = 64
    ctx.font = '24px Inter, sans-serif'
    ctx.fillStyle = color
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    const displayText = text.length > 12 ? text.slice(0, 11) + '...' : text
    ctx.fillText(displayText, 128, 32)

    const texture = new THREE.CanvasTexture(canvas)
    const material = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      depthTest: false,
    })
    const sprite = new THREE.Sprite(material)
    sprite.scale.set(30, 8, 1)
    return sprite
  }

  function createNodeObject(node: GraphNode): THREE.Object3D {
    const group = new THREE.Group()
    
    // Create label sprite
    const label = createTextSprite(node.name, node.color || '#60a5fa')
    label.position.y = 12
    label.visible = showNodeLabels.value
    group.add(label)
    
    // Store reference for visibility toggling
    nodeLabelSprites.set(node.id, label)
    
    return group
  }

  function initGraph() {
    if (!containerRef.value || isInitialized.value) {
      console.log('[useForceGraph] initGraph skipped - container not ready or already initialized')
      return
    }

    const elem = containerRef.value
    const width = elem.clientWidth || 800
    const height = elem.clientHeight || 600

    console.log('[useForceGraph] initializing graph with size:', width, 'x', height)

    // Create ForceGraph3D instance
    console.log('[useForceGraph] creating ForceGraph3D instance...')
    // ForceGraph3D is a Kapsule-based class — must use `new` to bind DOM element
    const ForceGraph3DCtor = ForceGraph3D as unknown as new (elem: HTMLElement) => ForceGraphInstance
    const graph = new ForceGraph3DCtor(elem)
      .width(width)
      .height(height)
      .backgroundColor('rgba(0,0,0,0)')
      .showNavInfo(false)
      .nodeThreeObject((node: GraphNode) => createNodeObject(node))
      .nodeThreeObjectExtend(true)
      .nodeColor((node: GraphNode) => getNodeColor(node))
      .nodeRelSize(6)
      .nodeResolution(16)
      .nodeOpacity(0.9)
      .linkWidth((link: GraphLink) => getLinkWidth(link))
      .linkColor((link: GraphLink) => getLinkColor(link))
      .linkOpacity(0.4)
      .linkDirectionalArrowLength(6)
      .linkDirectionalArrowRelPos(1)
      .linkDirectionalArrowColor(() => '#60a5fa')
      .linkCurvature(0.1)
      .enableNodeDrag(true)
      .enableNavigationControls(true)
      .onNodeClick(handleNodeClick)
      .onNodeRightClick(handleNodeRightClick)
      .onNodeHover(handleNodeHover)
      .onBackgroundClick(handleBackgroundClick)
      .warmupTicks(50)
      .cooldownTicks(100)

    // Configure force simulation
    const chargeForce = graph.d3Force('charge')
    if (chargeForce) {
      (chargeForce as unknown as { strength: (s: number) => void }).strength(-300)
    }
    
    const linkForce = graph.d3Force('link')
    if (linkForce) {
      (linkForce as unknown as { distance: (d: number) => void }).distance(80)
    }
    
    // Store instance
    graphInstance.value = graph
    isInitialized.value = true
    console.log('[useForceGraph] ForceGraph3D instance created and stored')

    // Handle resize
    const resizeObserver = new ResizeObserver(() => {
      if (!graphInstance.value || !containerRef.value) return
      const w = containerRef.value.clientWidth
      const h = containerRef.value.clientHeight
      graphInstance.value.width(w)
      graphInstance.value.height(h)
    })
    resizeObserver.observe(elem)

    // Initial data load
    console.log('[useForceGraph] store has', graphStore.nodes.length, 'nodes and', graphStore.links.length, 'links')
    refreshGraph()

    // Setup keyboard shortcut for toggling node labels
    // S key: only shows labels (when hidden)
    // H key: only hides labels (when shown)
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 's' || event.key === 'S') {
        if (!showNodeLabels.value) {
          setNodeLabelsVisible(true)
        }
      } else if (event.key === 'h' || event.key === 'H') {
        if (showNodeLabels.value) {
          setNodeLabelsVisible(false)
        }
      }
    }
    document.addEventListener('keydown', handleKeyDown)

    return () => {
      resizeObserver.disconnect()
      document.removeEventListener('keydown', handleKeyDown)
    }
  }

  function setNodeLabelsVisible(visible: boolean) {
    showNodeLabels.value = visible
    console.log('[useForceGraph] node labels:', visible ? 'shown' : 'hidden')
    nodeLabelSprites.forEach((sprite) => {
      sprite.visible = visible
    })
  }

  function getNodeColor(node: GraphNode): string {
    // Glow animation for unlocked nodes
    if (graphStore.glowNodeId === node.id && glowPhase.value > 0) {
      return glowPhase.value % 2 === 0 ? '#fbbf24' : '#ffffff'
    }
    // Highlight selected node
    if (graphStore.selectedNode?.id === node.id) {
      return '#fbbf24' // Amber for selected
    }
    // Highlight hovered node
    if (hoveredNodeId.value === node.id) {
      return '#f472b6' // Pink for hovered
    }
    // Highlight connected nodes
    if (highlightedNodeId.value) {
      const isConnected = isNodeConnected(node.id, highlightedNodeId.value)
      return isConnected ? node.color : '#334155' // Dim unconnected nodes
    }
    return node.color || '#60a5fa'
  }

  function getLinkWidth(link: GraphLink): number {
    if (highlightedNodeId.value) {
      const sourceId = typeof link.source === 'string' ? link.source : link.source.id
      const targetId = typeof link.target === 'string' ? link.target : link.target.id
      if (sourceId === highlightedNodeId.value || targetId === highlightedNodeId.value) {
        return 2
      }
      return 0.5
    }
    return 1 + (link.weight || 1) * 0.5
  }

  function getLinkColor(link: GraphLink): string {
    if (highlightedNodeId.value) {
      const sourceId = typeof link.source === 'string' ? link.source : link.source.id
      const targetId = typeof link.target === 'string' ? link.target : link.target.id
      if (sourceId === highlightedNodeId.value || targetId === highlightedNodeId.value) {
        return '#60a5fa'
      }
      return '#1e293b' // Dim unconnected links
    }
    return '#60a5fa'
  }

  function isNodeConnected(nodeId: string, targetId: string): boolean {
    if (nodeId === targetId) return true
    return allLinks.value.some(link => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source.id
      const linkTargetId = typeof link.target === 'string' ? link.target : link.target.id
      return (sourceId === nodeId && linkTargetId === targetId) || 
             (sourceId === targetId && linkTargetId === nodeId)
    })
  }

  function getVisibleNodes(): GraphNode[] {
    return allNodes.value
  }

  function getVisibleLinks(): GraphLink[] {
    return allLinks.value
  }

  function getChildNodeIds(parentId: string): string[] {
    const children = new Set<string>()
    const visited = new Set<string>()
    
    function traverse(currentId: string) {
      if (visited.has(currentId)) return
      visited.add(currentId)
      
      for (const link of allLinks.value) {
        const sourceId = typeof link.source === 'string' ? link.source : link.source.id
        const targetId = typeof link.target === 'string' ? link.target : link.target.id
        
        if (sourceId === currentId && !visited.has(targetId)) {
          children.add(targetId)
          traverse(targetId)
        }
      }
    }
    
    traverse(parentId)
    children.delete(parentId)
    return Array.from(children)
  }

  function handleNodeClick(node: GraphNode, event: MouseEvent) {
    event.stopPropagation()
    
    // Select node
    graphStore.selectedNode = node
    
    // Focus on node (camera animation)
    focusOnNode(node)
  }

  function handleNodeRightClick(node: GraphNode, event: MouseEvent) {
    event.preventDefault()
    event.stopPropagation()
    
    // Toggle collapse/expand
    toggleNodeCollapse(node.id)
  }

  function handleNodeHover(node: GraphNode | null) {
    hoveredNodeId.value = node?.id || null
    
    // Update cursor
    if (containerRef.value) {
      containerRef.value.style.cursor = node ? 'pointer' : 'default'
    }
    
    // Refresh graph to update colors
    if (graphInstance.value) {
      graphInstance.value.refresh()
    }
  }

  function handleBackgroundClick() {
    graphStore.selectedNode = null
    highlightedNodeId.value = null
    
    if (graphInstance.value) {
      graphInstance.value.refresh()
    }
  }

  function toggleNodeCollapse(nodeId: string) {
    if (collapsedNodes.value.has(nodeId)) {
      collapsedNodes.value.delete(nodeId)
    } else {
      collapsedNodes.value.add(nodeId)
    }
    updateGraphData()
  }

  function focusOnNode(node: GraphNode, transitionMs: number = 1000) {
    if (!graphInstance.value) return
    
    const distance = 120
    const nodeX = node.x || 0
    const nodeY = node.y || 0
    const nodeZ = node.z || 0
    const distRatio = 1 + distance / Math.hypot(nodeX, nodeY, nodeZ + distance)
    
    graphInstance.value.cameraPosition(
      { 
        x: nodeX * distRatio, 
        y: nodeY * distRatio, 
        z: (nodeZ + distance) * distRatio 
      },
      { x: nodeX, y: nodeY, z: nodeZ },
      transitionMs
    )
  }

  function resetCamera(transitionMs: number = 1000) {
    if (!graphInstance.value) return
    
    graphInstance.value.cameraPosition(
      { x: 0, y: 0, z: 300 },
      { x: 0, y: 0, z: 0 },
      transitionMs
    )
  }

  function zoomToFit(transitionMs: number = 1000) {
    if (!graphInstance.value) return
    graphInstance.value.zoomToFit(transitionMs, 50)
  }

  function setAutoRotate(enabled: boolean) {
    if (!graphInstance.value) return
    const controls = graphInstance.value.controls()
    if (controls) {
      controls.autoRotate = enabled
      controls.autoRotateSpeed = 1.0
    }
  }

  function updateGraphData() {
    if (!graphInstance.value) return
    
    const visibleNodes = getVisibleNodes()
    const visibleLinks = getVisibleLinks()
    
    graphInstance.value.graphData({
      nodes: visibleNodes,
      links: visibleLinks
    })
  }

  function refreshGraph() {
    if (!graphInstance.value) {
      console.log('[useForceGraph] refreshGraph skipped - graph not initialized')
      return
    }
    
    console.log('[useForceGraph] refreshGraph called, nodes:', graphStore.nodes.length, 'links:', graphStore.links.length)
    
    // Update internal data
    allNodes.value = graphStore.nodes.map(n => ({ 
      ...n, 
      val: n.size || 1 
    } as GraphNode))
    
    allLinks.value = graphStore.links.map(l => ({ 
      id: l.id,
      source: l.source_node_id,
      target: l.target_node_id,
      relationship: l.relationship,
      confidence: l.confidence,
      confidence_score: l.confidence_score,
      weight: l.weight
    } as GraphLink))
    
    console.log('[useForceGraph] updating graph data:', allNodes.value.length, 'nodes,', allLinks.value.length, 'links')
    updateGraphData()
  }

  // Watch for store changes - refresh graph whenever data changes
  watch(
    () => [graphStore.nodes.length, graphStore.links.length],
    ([newNodes, newLinks], [oldNodes, oldLinks]) => {
      console.log('[useForceGraph] data changed: nodes', oldNodes, '->', newNodes, ', links', oldLinks, '->', newLinks)
      if (newNodes > 0 || newLinks > 0) {
        refreshGraph()
      }
    },
  )

  watch(() => graphStore.selectedNode, () => {
    if (graphInstance.value) {
      graphInstance.value.refresh()
    }
  })

  // Watch for glow node changes - trigger glow animation
  watch(() => graphStore.glowNodeId, (nodeId) => {
    if (!nodeId || !graphInstance.value) {
      glowPhase.value = 0
      return
    }
    // Find and focus on the glowing node
    const node = allNodes.value.find(n => n.id === nodeId)
    if (node) {
      focusOnNode(node, 1500)
    }
    // Start glow animation: cycle 8 times over ~3.2s
    let count = 0
    const interval = setInterval(() => {
      count++
      glowPhase.value = count
      if (graphInstance.value) {
        graphInstance.value.refresh()
      }
      if (count >= 8) {
        clearInterval(interval)
        glowPhase.value = 0
        if (graphInstance.value) {
          graphInstance.value.refresh()
        }
      }
    }, 400)
  })

  // Cleanup
  onBeforeUnmount(() => {
    if (graphInstance.value) {
      // Clean up the graph instance
      const graph = graphInstance.value as unknown as { _destructor?: () => void }
      if (graph._destructor) {
        graph._destructor()
      }
    }
  })

  function showNodeLabelsAction() {
    if (!showNodeLabels.value) {
      setNodeLabelsVisible(true)
    }
  }

  function hideNodeLabelsAction() {
    if (showNodeLabels.value) {
      setNodeLabelsVisible(false)
    }
  }

  return {
    graphInstance,
    isInitialized,
    initGraph,
    resetCamera,
    zoomToFit,
    setAutoRotate,
    focusOnNode,
    toggleNodeCollapse,
    collapsedNodes,
    refreshGraph,
    getChildNodeIds,
    showNodeLabelsAction,
    hideNodeLabelsAction,
    showNodeLabels,
  }
}
