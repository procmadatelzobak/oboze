/**
 * Ó bože - Game Engine
 * Handles canvas rendering and entity animation
 */

class GameEngine {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');

        // Map size in game units (larger map = entities appear smaller relative to map)
        this.mapSize = 100;

        // Calculate canvas size (square, fit to viewport)
        this.resize();
        window.addEventListener('resize', () => this.resize());

        // Entity state
        this.entities = {};

        // Animation state
        this.animating = false;
        this.animationCommands = [];
        this.animationStep = 0;
        this.onAnimationComplete = null;

        // Start render loop
        this.render();
    }

    resize() {
        // Make canvas as large as possible - fill the right panel
        const padding = 20;
        const availableHeight = window.innerHeight - padding;
        // Use 75% of viewport width for map (chat panel is only 25%)
        const availableWidth = window.innerWidth * 0.75 - padding;
        const size = Math.min(availableHeight, availableWidth);

        this.canvas.width = size;
        this.canvas.height = size;
        this.scale = size / this.mapSize;
    }

    /**
     * Load entities from scenario
     */
    loadEntities(entitiesData) {
        this.entities = {};

        if (entitiesData && typeof entitiesData === 'object') {
            // Handle both array and object formats
            const entityList = Array.isArray(entitiesData)
                ? entitiesData
                : Object.values(entitiesData);

            for (const entity of entityList) {
                this.entities[entity.id] = {
                    id: entity.id,
                    name: entity.name,
                    x: entity.position?.x ?? entity.x ?? 50,
                    y: entity.position?.y ?? entity.y ?? 50,
                    radius: entity.radius || 5,
                    listensToPlayer: entity.listensToPlayer || false,
                    alive: entity.alive !== false
                };
            }
        }
    }

    /**
     * Reset entities to initial state
     */
    reset() {
        this.animating = false;
        this.animationCommands = [];
        this.animationStep = 0;
        this.commandStates = [];
    }

    /**
     * Start animation from commands
     */
    startAnimation(animationData, onComplete) {
        if (!animationData) return;

        // Load initial entity states
        if (animationData.entities) {
            this.loadEntities(animationData.entities);
        }

        // Prepare animation commands
        this.animationCommands = animationData.commands || [];
        this.animationStep = 0;
        this.animating = true;
        this.onAnimationComplete = onComplete;

        // Calculate total steps for all commands
        this.commandStates = this.animationCommands.map(cmd => ({
            cmd: cmd,
            currentStep: 0,
            started: false,
            completed: false
        }));

        this.animate();
    }

    /**
     * Animation loop
     */
    animate() {
        if (!this.animating) return;

        let allCompleted = true;

        for (const state of this.commandStates) {
            if (state.completed) continue;

            const cmd = state.cmd;
            const entity = this.entities[cmd.entityId];
            if (!entity || !entity.alive) {
                state.completed = true;
                continue;
            }

            // Check delay
            if (this.animationStep < (cmd.delay || 0)) {
                allCompleted = false;
                continue;
            }

            state.started = true;

            // Execute action
            if (cmd.action === 'move' && cmd.direction) {
                if (state.currentStep < cmd.steps) {
                    // Move entity
                    entity.x += cmd.direction.x * (cmd.speed || 1);
                    entity.y += cmd.direction.y * (cmd.speed || 1);
                    state.currentStep++;
                    allCompleted = false;

                    // Check if out of bounds
                    if (entity.x < -entity.radius || entity.x > this.mapSize + entity.radius ||
                        entity.y < -entity.radius || entity.y > this.mapSize + entity.radius) {
                        entity.alive = false;
                        state.completed = true;
                    }
                } else {
                    state.completed = true;
                }
            } else if (cmd.action === 'wait') {
                // Wait action - entity stays in place for a number of steps
                if (state.currentStep < cmd.steps) {
                    state.currentStep++;
                    allCompleted = false;
                } else {
                    state.completed = true;
                }
            } else if (cmd.action === 'disappear') {
                entity.alive = false;
                state.completed = true;
            }
        }

        this.animationStep++;

        if (allCompleted) {
            this.animating = false;
            if (this.onAnimationComplete) {
                this.onAnimationComplete();
            }
        } else {
            // Continue animation at ~60fps
            setTimeout(() => this.animate(), 16);
        }
    }

    /**
     * Render loop
     */
    render() {
        const ctx = this.ctx;
        const scale = this.scale;

        // Clear canvas
        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw border
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1;
        ctx.strokeRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw grid (subtle)
        ctx.strokeStyle = '#222222';
        ctx.lineWidth = 0.5;
        for (let i = 10; i < this.mapSize; i += 10) {
            const pos = i * scale;
            ctx.beginPath();
            ctx.moveTo(pos, 0);
            ctx.lineTo(pos, this.canvas.height);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(0, pos);
            ctx.lineTo(this.canvas.width, pos);
            ctx.stroke();
        }

        // Draw entities
        for (const id in this.entities) {
            const entity = this.entities[id];
            if (!entity.alive) continue;

            const x = entity.x * scale;
            const y = entity.y * scale;
            const r = entity.radius * scale;

            // Draw circle
            ctx.beginPath();
            ctx.arc(x, y, r, 0, Math.PI * 2);
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = entity.listensToPlayer ? 2 : 1;
            ctx.stroke();

            // If entity listens to player, draw inner dot
            if (entity.listensToPlayer) {
                ctx.beginPath();
                ctx.arc(x, y, r * 0.3, 0, Math.PI * 2);
                ctx.fillStyle = '#ffffff';
                ctx.fill();
            }

            // Draw name below entity
            ctx.fillStyle = '#888888';
            ctx.font = `${Math.max(10, 12 * scale / 5)}px Courier New`;
            ctx.textAlign = 'center';
            ctx.fillText(entity.name, x, y + r + 15);
        }

        // Continue render loop
        requestAnimationFrame(() => this.render());
    }
}
