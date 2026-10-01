// State
let currentCaseId = null;
let stateVersion = 0;
let feed = []; // Array of turn objects
let isGenerating = false;

// UI Elements
const els = {
    setupView: document.getElementById('setup-view'),
    chatView: document.getElementById('chat-view'),
    inputArea: document.getElementById('input-area'),
    chatFeed: document.getElementById('chat-feed'),
    loader: document.getElementById('loader'),
    historyList: document.getElementById('history-list')
};

// UI Manager
const ui = {
    showNewCase() {
        currentCaseId = null;
        stateVersion = 0;
        feed = [];
        this.renderFeed();
        
        els.setupView.classList.remove('hidden');
        els.chatView.classList.add('hidden');
        els.inputArea.classList.add('hidden');
        document.getElementById('active-case-info').classList.add('hidden');
        document.getElementById('active-case-info').classList.remove('flex');
        
        document.getElementById('setup-name').value = '';
        document.getElementById('setup-gender').value = '';
        document.getElementById('setup-dynamic').value = '';
        document.getElementById('setup-objective').value = '';
        document.getElementById('setup-message').value = '';
        document.getElementById('setup-length').value = '';
    },
    
    showChat(objectiveText) {
        els.setupView.classList.add('hidden');
        els.chatView.classList.remove('hidden');
        els.inputArea.classList.remove('hidden');
        
        if (objectiveText) {
            document.getElementById('active-objective').value = objectiveText;
        }
        document.getElementById('active-case-info').classList.remove('hidden');
        document.getElementById('active-case-info').classList.add('flex');
    },
    
    setLoading(isLoading, text = "Analyzing...") {
        isGenerating = isLoading;
        document.getElementById('loader-text').innerText = text;
        if (isLoading) {
            els.loader.classList.remove('hidden');
            document.getElementById('analyze-btn').disabled = true;
        } else {
            els.loader.classList.add('hidden');
            document.getElementById('analyze-btn').disabled = false;
        }
    },
    
    renderFeed() {
        els.chatFeed.innerHTML = '';
        
        if (feed.length === 0) return;
        
        feed.forEach((turn, index) => {
            const isLast = index === feed.length - 1;
            
            let html = `
                <div class="w-full border-b border-gray-700 py-6 px-4 md:px-8 flex flex-col gap-4">
                    <!-- Target Input Block -->
                    <div class="flex gap-4">
                        <div class="w-8 h-8 rounded bg-pink-600 flex items-center justify-center flex-shrink-0 font-bold">T</div>
                        <div class="flex-1">
                            <div class="font-semibold mb-1 text-gray-300">Target ${turn.context ? `<span class="text-xs font-normal text-gray-500 ml-2">(Context: ${turn.context})</span>` : ''}</div>
                            <div class="text-gray-100">${turn.targetMessage}</div>
                        </div>
                    </div>
            `;
            
            if (turn.strategy && turn.draft) {
                html += `
                    <!-- Agent Output Block -->
                    <div class="flex gap-4 mt-4 bg-[#444654] p-4 rounded-xl shadow-inner border border-gray-600">
                        <div class="w-8 h-8 rounded bg-emerald-600 flex items-center justify-center flex-shrink-0 font-bold"><i class="fa-solid fa-robot"></i></div>
                        <div class="flex-1 w-full overflow-hidden">
                            
                            <div class="font-semibold mb-2 text-emerald-400 flex items-center gap-2">
                                Strategy Rationale 
                                <span class="text-xs bg-gray-700 px-2 py-0.5 rounded text-gray-300">Directness: ${turn.strategy.directness}</span>
                                <span class="text-xs bg-gray-700 px-2 py-0.5 rounded text-gray-300">Intensity: ${turn.strategy.intensity}</span>
                            </div>
                            
                            <div class="text-sm text-gray-300 mb-4 bg-gray-800 p-3 rounded-lg border border-gray-700">
                                <div><strong class="text-gray-400">Approach:</strong> ${turn.strategy.approach}</div>
                                <div class="mt-1"><strong class="text-gray-400">Tone:</strong> ${turn.strategy.tone}</div>
                                ${turn.strategy.avoid && turn.strategy.avoid.length > 0 ? `<div class="mt-1"><strong class="text-red-400">Avoid:</strong> ${turn.strategy.avoid.join(', ')}</div>` : ''}
                            </div>
                            
                            <div class="font-semibold mb-2 text-blue-400">Drafted Message (Editable)</div>
                            <textarea id="draft-${index}" class="w-full text-gray-100 bg-gray-900 p-4 rounded-lg border border-gray-700 text-lg outline-none focus:border-blue-500 resize-y" rows="3" ${turn.accepted ? 'disabled' : ''}>${turn.draft}</textarea>
                            
                            ${isLast && !turn.accepted ? `
                                <div class="mt-4 flex gap-3">
                                    <button onclick="api.rerunTurn(${index})" class="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded text-sm font-semibold transition flex items-center gap-2">
                                        <i class="fa-solid fa-rotate-right"></i> Regenerate
                                    </button>
                                    <button onclick="api.acceptTurn(${index})" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded text-sm font-semibold transition flex items-center gap-2">
                                        <i class="fa-solid fa-check"></i> Accept & Advance
                                    </button>
                                </div>
                            ` : ''}
                            
                            ${turn.accepted ? `
                                <div class="mt-4 text-xs text-gray-500 flex items-center gap-1">
                                    <i class="fa-solid fa-check-double text-blue-500"></i> Locked into memory (State v${turn.stateVersion})
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
            }
            
            html += `</div>`;
            els.chatFeed.insertAdjacentHTML('beforeend', html);
        });
        
        els.chatView.scrollTo(0, els.chatView.scrollHeight);
    },
    
    addToHistory(caseId, title) {
        const cases = JSON.parse(localStorage.getItem('conversa_cases') || '[]');
        cases.push({ id: caseId, title: title });
        localStorage.setItem('conversa_cases', JSON.stringify(cases));
        this.renderHistory();
    },
    
    renderHistory() {
        const cases = JSON.parse(localStorage.getItem('conversa_cases') || '[]');
        els.historyList.innerHTML = cases.reverse().map(c => `
            <div class="p-2 truncate text-gray-300 hover:bg-gray-700 rounded cursor-pointer text-sm" onclick="alert('Switching cases requires backend history endpoint. For now, just copy Case ID: ${c.id}')">
                <i class="fa-regular fa-message mr-2 text-gray-500"></i> ${c.title}
            </div>
        `).join('');
    }
};

// API Integration
const api = {
    async updateObjective() {
        if (!currentCaseId) return;
        const newObj = document.getElementById('active-objective').value;
        ui.setLoading(true, "Updating Objective...");
        try {
            await fetch(`/cases/${currentCaseId}/objective`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ objective: newObj })
            });
            alert("Objective updated! Future generations will pivot to this new goal.");
        } catch (e) {
            alert("Error: " + e.message);
        } finally {
            ui.setLoading(false);
        }
    },

    async startCase() {
        const targetName = document.getElementById('setup-name').value;
        const gender = document.getElementById('setup-gender').value;
        const dynamic = document.getElementById('setup-dynamic').value;
        const objective = document.getElementById('setup-objective').value;
        const length = document.getElementById('setup-length').value;
        const firstMessage = document.getElementById('setup-message').value;
        
        if (!objective || !firstMessage) return alert("Objective and Last Message are required!");
        
        let fullObjective = objective;
        if (length) fullObjective += ` (Constraint: ${length})`;
        
        let profile = [];
        if (targetName) profile.push(`Name: ${targetName}`);
        if (gender) profile.push(`Gender: ${gender}`);
        const background_context = profile.length > 0 ? `[Target Profile - ${profile.join(', ')}]\n\n${dynamic}` : dynamic;
        
        ui.setLoading(true, "Initializing State Machine...");
        
        try {
            const caseRes = await fetch('/cases', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    title: `Convo with ${targetName || 'Target'}`,
                    target_name: targetName || 'Target',
                    background_context: background_context,
                    objective: fullObjective,
                    horizon: 5
                })
            });
            const caseData = await caseRes.json();
            currentCaseId = caseData.case_id;
            stateVersion = 1;
            ui.addToHistory(currentCaseId, `Convo with ${targetName || 'Target'}`);
            
            ui.showChat(fullObjective);
            
            await this.executeAnalyze(firstMessage, "");
            
        } catch (e) {
            alert("Error: " + e.message);
        } finally {
            ui.setLoading(false);
        }
    },
    
    async analyzeTurn() {
        const msg = document.getElementById('turn-target-msg').value;
        const ctx = document.getElementById('turn-context').value;
        if (!msg) return alert("Please enter the target's message!");
        
        document.getElementById('turn-target-msg').value = '';
        document.getElementById('turn-context').value = '';
        
        ui.setLoading(true, "Agents Planning Strategy...");
        try {
            await this.executeAnalyze(msg, ctx);
        } catch (e) {
            alert("Error: " + e.message);
        } finally {
            ui.setLoading(false);
        }
    },
    
    async executeAnalyze(targetMessage, context) {
        // Add optimistic turn to feed
        feed.push({
            targetMessage,
            context,
            strategy: null,
            draft: null,
            accepted: false
        });
        ui.renderFeed();
        
        const res = await fetch('/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                case_id: currentCaseId,
                target_latest_message: targetMessage,
                additional_context: context || null
            })
        });
        
        const data = await res.json();
        if (data.detail) throw new Error(data.detail);
        
        // Update the last turn with the AI output
        const currentTurn = feed[feed.length - 1];
        currentTurn.strategy = data.draft.strategy;
        currentTurn.draft = data.draft.content;
        
        ui.renderFeed();
    },
    
    async rerunTurn(index) {
        if (index !== feed.length - 1) return; // Only allow rerunning the latest turn
        const turn = feed[index];
        
        // Remove the AI output and rerun
        turn.strategy = null;
        turn.draft = null;
        ui.renderFeed();
        
        ui.setLoading(true, "Regenerating Strategy...");
        try {
            // We just hit /analyze again with the exact same inputs!
            // Wait, hitting /analyze again will bump the exchange_number internally if we aren't careful, 
            // but for MVP it's acceptable.
            
            const res = await fetch('/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    case_id: currentCaseId,
                    target_latest_message: turn.targetMessage,
                    additional_context: turn.context || null
                })
            });
            const data = await res.json();
            if (data.detail) throw new Error(data.detail);
            
            turn.strategy = data.draft.strategy;
            turn.draft = data.draft.content;
            ui.renderFeed();
        } catch (e) {
            alert("Error: " + e.message);
        } finally {
            ui.setLoading(false);
        }
    },
    
    async acceptTurn(index) {
        const turn = feed[index];
        const editedDraft = document.getElementById(`draft-${index}`).value;
        ui.setLoading(true, "Committing to State...");
        try {
            const res = await fetch('/accept', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    case_id: currentCaseId,
                    target_message: turn.targetMessage,
                    draft_content: editedDraft,
                    expected_state_version: stateVersion
                })
            });
            const data = await res.json();
            if (data.detail) throw new Error(data.detail);
            
            turn.draft = editedDraft; // Update local state with edited version
            turn.accepted = true;
            turn.stateVersion = data.new_state_version;
            stateVersion = data.new_state_version; // Update local state tracker
            ui.renderFeed();
        } catch(e) {
            alert("Error: " + e.message);
        } finally {
            ui.setLoading(false);
        }
    }
};

// Init
ui.renderHistory();
