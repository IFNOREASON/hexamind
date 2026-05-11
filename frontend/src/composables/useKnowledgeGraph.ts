import { watch, type Ref } from 'vue'
import * as THREE from 'three'
import { useGraphStore } from '@/stores/graph'
import type { ThreeContext } from './useThreeScene'
import type { KnowledgeNode, KnowledgeLink } from '@/types/graph'

interface NodeObject {
  mesh: THREE.Mesh
  label: THREE.Sprite
  node: KnowledgeNode
  velocity: THREE.Vector3
  position: THREE.Vector3
}

interface LinkObject {
  line: THREE.Line
  link: KnowledgeLink
}

export function useKnowledgeGraph(
  context: Ref<ThreeContext | null>,
  onAnimate: (cb: (delta: number) => void) => void,
) {
  const graphStore = useGraphStore()
  const nodeObjects = new Map<string, NodeObject>()
  const linkObjects = new Map<number, LinkObject>()
  const graphGroup = new THREE.Group()
  const raycaster = new THREE.Raycaster()
  const mouse = new THREE.Vector2()
  let initialized = false

  function initGroup() {
    if (!context.value || initialized) return
    context.value.scene.add(graphGroup)
    initialized = true

    // Click handler for node selection
    context.value.renderer.domElement.addEventListener('click', onCanvasClick)
  }

  function createNodeMesh(node: KnowledgeNode): NodeObject {
    const radius = 3 + node.size * 2
    const geometry = new THREE.SphereGeometry(radius, 32, 32)
    const color = new THREE.Color(node.color || '#60a5fa')
    const material = new THREE.MeshPhongMaterial({
      color,
      emissive: color,
      emissiveIntensity: 0.3,
      transparent: true,
      opacity: 0.9,
    })
    const mesh = new THREE.Mesh(geometry, material)
    mesh.userData = { nodeId: node.id }

    // Glow ring
    const glowGeometry = new THREE.RingGeometry(radius + 1, radius + 2.5, 32)
    const glowMaterial = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: 0.15,
      side: THREE.DoubleSide,
    })
    const glow = new THREE.Mesh(glowGeometry, glowMaterial)
    glow.lookAt(0, 0, 1)
    mesh.add(glow)

    // Label sprite
    const label = createTextSprite(node.name, color)
    label.position.y = radius + 6

    // Random initial position
    const position = new THREE.Vector3(
      (Math.random() - 0.5) * 150,
      (Math.random() - 0.5) * 100,
      (Math.random() - 0.5) * 150,
    )
    mesh.position.copy(position)
    label.position.add(position)

    // Enter animation: scale from 0
    mesh.scale.setScalar(0)
    label.scale.setScalar(0)

    graphGroup.add(mesh)
    graphGroup.add(label)

    return {
      mesh,
      label,
      node,
      velocity: new THREE.Vector3(),
      position,
    }
  }

  function createTextSprite(text: string, color: THREE.Color): THREE.Sprite {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')!
    canvas.width = 256
    canvas.height = 64
    ctx.font = '24px Inter, sans-serif'
    ctx.fillStyle = `rgb(${Math.round(color.r * 255)}, ${Math.round(color.g * 255)}, ${Math.round(color.b * 255)})`
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

  function createLinkLine(link: KnowledgeLink): LinkObject | null {
    const sourceObj = nodeObjects.get(link.source_node_id)
    const targetObj = nodeObjects.get(link.target_node_id)
    if (!sourceObj || !targetObj) return null

    const geometry = new THREE.BufferGeometry()
    const positions = new Float32Array(6)
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))

    const opacity = 0.1 + link.confidence_score * 0.4
    const material = new THREE.LineBasicMaterial({
      color: 0x60a5fa,
      transparent: true,
      opacity,
    })
    const line = new THREE.Line(geometry, material)
    graphGroup.add(line)

    return { line, link }
  }

  function updateLinkPositions() {
    for (const [, linkObj] of linkObjects) {
      const sourceObj = nodeObjects.get(linkObj.link.source_node_id)
      const targetObj = nodeObjects.get(linkObj.link.target_node_id)
      if (!sourceObj || !targetObj) continue

      const positions = linkObj.line.geometry.attributes.position as THREE.BufferAttribute
      positions.setXYZ(0, sourceObj.position.x, sourceObj.position.y, sourceObj.position.z)
      positions.setXYZ(1, targetObj.position.x, targetObj.position.y, targetObj.position.z)
      positions.needsUpdate = true
    }
  }

  // Simple force-directed layout step
  function forceStep(delta: number) {
    const nodes = Array.from(nodeObjects.values())
    if (nodes.length === 0) return

    const repulsion = 800
    const attraction = 0.005
    const damping = 0.92
    const center = 0.001

    // Repulsion between all node pairs
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const diff = new THREE.Vector3().subVectors(nodes[i].position, nodes[j].position)
        const dist = Math.max(diff.length(), 1)
        const force = diff.normalize().multiplyScalar(repulsion / (dist * dist))
        nodes[i].velocity.add(force)
        nodes[j].velocity.sub(force)
      }
    }

    // Attraction along edges
    for (const [, linkObj] of linkObjects) {
      const source = nodeObjects.get(linkObj.link.source_node_id)
      const target = nodeObjects.get(linkObj.link.target_node_id)
      if (!source || !target) continue

      const diff = new THREE.Vector3().subVectors(target.position, source.position)
      const dist = diff.length()
      const force = diff.normalize().multiplyScalar(dist * attraction)
      source.velocity.add(force)
      target.velocity.sub(force)
    }

    // Center gravity
    for (const node of nodes) {
      const toCenter = node.position.clone().negate().multiplyScalar(center)
      node.velocity.add(toCenter)
    }

    // Apply velocity
    for (const node of nodes) {
      node.velocity.multiplyScalar(damping)
      node.position.add(node.velocity.clone().multiplyScalar(Math.min(delta, 0.05) * 60))
      node.mesh.position.copy(node.position)
      node.label.position.copy(node.position)
      node.label.position.y += (3 + node.node.size * 2) + 6

      // Enter animation
      if (node.mesh.scale.x < 1) {
        const s = Math.min(node.mesh.scale.x + delta * 3, 1)
        node.mesh.scale.setScalar(s)
        node.label.scale.set(30 * s, 8 * s, 1)
      }
    }

    updateLinkPositions()
  }

  function onCanvasClick(event: MouseEvent) {
    if (!context.value) return
    const rect = context.value.renderer.domElement.getBoundingClientRect()
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

    raycaster.setFromCamera(mouse, context.value.camera)
    const meshes = Array.from(nodeObjects.values()).map((n) => n.mesh)
    const intersects = raycaster.intersectObjects(meshes)

    if (intersects.length > 0) {
      const nodeId = intersects[0].object.userData.nodeId
      const node = graphStore.nodes.find((n) => n.id === nodeId) ?? null
      graphStore.selectedNode = node
    } else {
      graphStore.selectedNode = null
    }
  }

  // Sync nodes/links from store
  function syncGraph() {
    if (!context.value) return
    initGroup()

    const currentNodeIds = new Set(graphStore.nodes.map((n) => n.id))
    const currentLinkIds = new Set(graphStore.links.map((l) => l.id))

    // Remove deleted nodes
    for (const [id, obj] of nodeObjects) {
      if (!currentNodeIds.has(id)) {
        graphGroup.remove(obj.mesh)
        graphGroup.remove(obj.label)
        obj.mesh.geometry.dispose()
        ;(obj.mesh.material as THREE.Material).dispose()
        nodeObjects.delete(id)
      }
    }

    // Remove deleted links
    for (const [id, obj] of linkObjects) {
      if (!currentLinkIds.has(id)) {
        graphGroup.remove(obj.line)
        obj.line.geometry.dispose()
        ;(obj.line.material as THREE.Material).dispose()
        linkObjects.delete(id)
      }
    }

    // Add new nodes
    for (const node of graphStore.nodes) {
      if (!nodeObjects.has(node.id)) {
        nodeObjects.set(node.id, createNodeMesh(node))
      }
    }

    // Add new links
    for (const link of graphStore.links) {
      if (!linkObjects.has(link.id)) {
        const obj = createLinkLine(link)
        if (obj) linkObjects.set(link.id, obj)
      }
    }
  }

  // Watch for store changes
  watch(
    () => [graphStore.nodes.length, graphStore.links.length],
    syncGraph,
    { immediate: true },
  )

  watch(
    () => context.value,
    (ctx) => {
      if (ctx) syncGraph()
    },
  )

  // Register animation callback
  onAnimate(forceStep)

  return {
    syncGraph,
    nodeObjects,
  }
}
