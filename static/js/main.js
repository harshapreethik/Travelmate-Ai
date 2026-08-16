/* TravelMate AI — Frontend Logic Manager */

document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------------
    // MARKDOWN FORMATTER (Clean hierarchy, No raw # markers)
    // -------------------------------------------------------------------
    function formatMarkdown(text) {
        if (!text) return "";
        let html = text
            .replace(/^(?:---|___|\*\*\*)$/gm, '<hr class="my-3 border-secondary-subtle">')
            .replace(/^#### (.*$)/gm, '<h6 class="fw-bold text-dark mt-3 mb-1">$1</h6>')
            .replace(/^### (.*$)/gm, '<h5 class="fw-bold text-primary mt-3 mb-2">$1</h5>')
            .replace(/^## (.*$)/gm, '<h4 class="fw-bold text-primary mt-4 mb-2">$1</h4>')
            .replace(/^# (.*$)/gm, '<h3 class="fw-bold text-primary mt-4 mb-3">$1</h3>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)/g, '<em>$1</em>')
            .replace(/^\s*[\*\-]\s+(.*)$/gm, '<li class="ms-3 mb-1">$1</li>')
            .replace(/\n{2,}/g, '<br><br>')
            .replace(/\n/g, '<br>');

        html = html.replace(/(<li class="ms-3 mb-1">[\s\S]*?<\/li>)/gm, '<ul class="mb-2 ps-2">$1</ul>');
        return html;
    }

    // -------------------------------------------------------------------
    // STREAMING / TYPEWRITER EFFECT
    // -------------------------------------------------------------------
    function streamTextWordByWord(element, fullText, speed = 20) {
        element.innerHTML = "";
        const words = fullText.split(/(\s+)/);
        let index = 0;
        let currentString = "";

        const interval = setInterval(() => {
            if (index < words.length) {
                currentString += words[index];
                element.innerHTML = formatMarkdown(currentString);
                chatWindow.scrollTop = chatWindow.scrollHeight;
                index++;
            } else {
                clearInterval(interval);
                element.innerHTML = formatMarkdown(fullText);
                chatWindow.scrollTop = chatWindow.scrollHeight;
            }
        }, speed);
    }

    // -------------------------------------------------------------------
    // 1. CHAT ASSISTANT HANDLER (Auto Language Detection)
    // -------------------------------------------------------------------
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");
    const chatWindow = document.getElementById("chatWindow");

    if (chatForm && chatInput && chatWindow) {
        chatForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const msg = chatInput.value.trim();
            if (!msg) return;

            appendChatBubble(msg, "user");
            chatInput.value = "";

            const loadingBubble = appendChatBubble("Thinking...", "bot");
            loadingBubble.innerHTML = '<span class="spinner-grow spinner-grow-sm me-2 text-primary" role="status"></span>Typing...';

            try {
                const res = await fetch("/api/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: msg })
                });
                const data = await res.json();
                
                if (data.status === "success") {
                    streamTextWordByWord(loadingBubble, data.reply, 20);
                } else {
                    loadingBubble.textContent = "Error: " + (data.message || "Failed to respond.");
                }
            } catch (err) {
                loadingBubble.textContent = "Connection error. Please try again.";
            }
        });
    }

    function appendChatBubble(text, sender) {
        const bubble = document.createElement("div");
        bubble.className = `chat-bubble ${sender}`;
        bubble.textContent = text;
        chatWindow.appendChild(bubble);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        return bubble;
    }

    // -------------------------------------------------------------------
    // 2. RECOMMENDATION ENGINE HANDLER (Interactive Structured Matrix)
    // -------------------------------------------------------------------
    const recForm = document.getElementById("recommendationForm");
    const recOutput = document.getElementById("recommendationsOutput");

    if (recForm && recOutput) {
        recForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            recOutput.innerHTML = `
                <div class="text-center p-5">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="mt-2 text-muted fw-semibold">Scoring & Curating Best Spots...</p>
                </div>
            `;

            const destination = document.getElementById("recDestination").value.trim();
            const interests = Array.from(document.querySelectorAll(".rec-interest:checked")).map(cb => cb.value);

            const payload = {
                destination: destination,
                traveller_type: document.getElementById("recTravellerType").value,
                budget_level: document.getElementById("recBudget").value,
                interests: interests
            };

            try {
                const res = await fetch("/api/recommendations", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();

                if (data.status === "success") {
                    const recs = data.data.recommendations || [];
                    const insights = data.data.ai_insights || "";

                    let outputHtml = "";

                    if (insights) {
                        outputHtml += `
                            <div class="card p-3 mb-4 border-0 shadow-sm bg-primary-subtle border-start border-primary border-4 rounded-3">
                                <div class="d-flex align-items-center mb-1">
                                    <i class="bi bi-stars text-primary fs-5 me-2"></i>
                                    <h6 class="fw-bold text-primary m-0">AI Curated Persona Fit</h6>
                                </div>
                                <p class="m-0 text-dark small">${formatMarkdown(insights)}</p>
                            </div>
                        `;
                    }

                    outputHtml += '<div class="row g-3">';

                    recs.forEach(item => {
                        const matchPct = Math.round((item.match_score || 0.9) * 100);
                        const mapQuery = encodeURIComponent(`${item.name}, ${destination}`);
                        const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${mapQuery}`;

                        outputHtml += `
                            <div class="col-md-6">
                                <div class="card h-100 p-3 shadow-sm border-0 rounded-3 d-flex flex-column justify-content-between position-relative">
                                    <div>
                                        <div class="d-flex justify-content-between align-items-start mb-2">
                                            <h5 class="fw-bold text-dark m-0 fs-6">${item.name}</h5>
                                            <span class="badge bg-success-subtle text-success border border-success-subtle px-2 py-1">
                                                <i class="bi bi-fire me-1"></i>${matchPct}% Match
                                            </span>
                                        </div>
                                        
                                        <div class="d-flex gap-2 mb-2">
                                            <span class="badge bg-light text-secondary border small">${item.category}</span>
                                            <span class="badge bg-light text-secondary border small"><i class="bi bi-clock me-1"></i>${item.duration || '1-2 hrs'}</span>
                                        </div>

                                        <p class="text-secondary small mb-2">${item.why_for_you || ''}</p>

                                        <div class="bg-light p-2 rounded-2 mb-2 small">
                                            <div class="text-muted"><i class="bi bi-wallet2 text-primary me-1"></i><strong>Cost:</strong> ${item.approx_cost || 'Free Entry'}</div>
                                            <div class="text-muted"><i class="bi bi-sun text-warning me-1"></i><strong>Best Timing:</strong> ${item.best_time_to_visit || 'Anytime'}</div>
                                        </div>

                                        ${item.insider_tip ? `
                                            <div class="p-2 rounded-2 border-start border-warning border-3 bg-warning-subtle text-dark small mb-3">
                                                <strong><i class="bi bi-lightbulb-fill text-warning me-1"></i>Local Secret:</strong> ${item.insider_tip}
                                            </div>
                                        ` : ''}
                                    </div>

                                    <div class="pt-2 border-top">
                                        <a href="${mapsUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-outline-primary w-100 fw-semibold">
                                            <i class="bi bi-geo-alt-fill me-1"></i>View Location on Google Maps
                                        </a>
                                    </div>
                                </div>
                            </div>
                        `;
                    });

                    outputHtml += '</div>';
                    recOutput.innerHTML = outputHtml;
                } else {
                    recOutput.innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
                }
            } catch (err) {
                recOutput.innerHTML = '<div class="alert alert-danger">Failed to load spot recommendations.</div>';
            }
        });
    }

    // -------------------------------------------------------------------
    // 3. ITINERARY BUILDER HANDLER
    // -------------------------------------------------------------------
    const itinForm = document.getElementById("itineraryForm");
    const itinOutput = document.getElementById("itineraryOutput");

    if (itinForm && itinOutput) {
        itinForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            itinOutput.innerHTML = '<div class="text-center p-4"><div class="spinner-border text-primary" role="status"></div></div>';

            const payload = {
                destination: document.getElementById("itinDestination").value,
                num_days: parseInt(document.getElementById("itinDays").value),
                budget_level: document.getElementById("itinBudget").value,
                traveller_type: document.getElementById("itinStyle").value
            };

            try {
                const res = await fetch("/api/itinerary", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();

                if (data.status === "success") {
                    itinOutput.innerHTML = `
                        <div class="card feature-card p-4 shadow-sm border-0">
                            <h6 class="fw-bold text-primary mb-3"><i class="bi bi-map me-2"></i>${data.data.num_days}-Day Itinerary for ${data.data.destination}</h6>
                            <div>${formatMarkdown(data.data.itinerary)}</div>
                        </div>
                    `;
                } else {
                    itinOutput.innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
                }
            } catch (err) {
                itinOutput.innerHTML = '<div class="alert alert-danger">Error generating itinerary.</div>';
            }
        });
    }

    // -------------------------------------------------------------------
    // 4. VISION / MENU OCR HANDLER
    // -------------------------------------------------------------------
    const visionFile = document.getElementById("visionFile");
    const imagePreviewContainer = document.getElementById("imagePreviewContainer");
    const imagePreview = document.getElementById("imagePreview");
    const visionForm = document.getElementById("visionForm");
    const visionOutput = document.getElementById("visionOutput");

    if (visionFile && imagePreview && imagePreviewContainer) {
        visionFile.addEventListener("change", () => {
            const file = visionFile.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    imagePreview.src = e.target.result;
                    imagePreviewContainer.style.display = "block";
                };
                reader.readAsDataURL(file);
            }
        });
    }

    if (visionForm && visionOutput) {
        visionForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const file = visionFile ? visionFile.files[0] : null;
            if (!file) return;

            visionOutput.innerHTML = '<div class="text-center p-4"><div class="spinner-border text-primary" role="status"></div><p class="mt-2 text-muted">Analyzing image with Gemini Vision...</p></div>';

            const formData = new FormData();
            formData.append("file", file);
            formData.append("destination", "Global / Any Destination");
            formData.append("user_query", document.getElementById("visionQuery") ? document.getElementById("visionQuery").value : "");

            try {
                const res = await fetch("/api/vision", {
                    method: "POST",
                    body: formData
                });
                const data = await res.json();

                if (data.status === "success") {
                    visionOutput.innerHTML = `
                        <div class="card feature-card p-4 shadow-sm border-0">
                            <h6 class="fw-bold text-primary mb-3"><i class="bi bi-eye me-2"></i>Vision Analysis Result</h6>
                            <div>${formatMarkdown(data.analysis)}</div>
                        </div>
                    `;
                } else {
                    visionOutput.innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
                }
            } catch (err) {
                visionOutput.innerHTML = '<div class="alert alert-danger">Error processing image.</div>';
            }
        });
    }

    // -------------------------------------------------------------------
    // 5. TRANSLATOR HANDLER (Auto-Detect)
    // -------------------------------------------------------------------
    const transForm = document.getElementById("translateForm");
    const transText = document.getElementById("transText");
    const transOutput = document.getElementById("translateOutput");
    const transMicBtn = document.getElementById("transMicBtn");

    document.querySelectorAll(".quick-phrase-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            if (transText) {
                transText.value = chip.getAttribute("data-phrase");
                transForm.dispatchEvent(new Event("submit"));
            }
        });
    });

    if (transMicBtn && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';

        transMicBtn.addEventListener("click", () => {
            recognition.start();
            transMicBtn.classList.add("btn-danger");
        });

        recognition.onresult = (event) => {
            transText.value = event.results[0][0].transcript;
            transMicBtn.classList.remove("btn-danger");
            transForm.dispatchEvent(new Event("submit"));
        };

        recognition.onerror = () => {
            transMicBtn.classList.remove("btn-danger");
        };
    }

    if (transForm && transOutput) {
        transForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const textToTranslate = transText.value.trim();
            if (!textToTranslate) return;

            transOutput.innerHTML = '<div class="text-center p-3"><div class="spinner-border text-primary" role="status"></div></div>';

            try {
                const res = await fetch("/api/translate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        text: textToTranslate,
                        destination: "Global / Any Destination"
                    })
                });
                const data = await res.json();

                if (data.status === "success") {
                    const rawText = data.data.translation_data || "";
                    
                    transOutput.innerHTML = `
                        <div class="card feature-card p-4 shadow-sm border-0">
                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <h6 class="fw-bold text-primary m-0"><i class="bi bi-check2-circle me-1"></i>Translation Result</h6>
                                <button class="btn btn-sm btn-outline-primary" id="playAudioBtn">
                                    <i class="bi bi-volume-up-fill me-1"></i>Listen (TTS)
                                </button>
                            </div>
                            <div class="fs-6">${formatMarkdown(rawText)}</div>
                        </div>
                    `;

                    const playBtn = document.getElementById("playAudioBtn");
                    if (playBtn && 'speechSynthesis' in window) {
                        playBtn.addEventListener("click", () => {
                            const cleanText = rawText.replace(/[*#]/g, '');
                            window.speechSynthesis.speak(new SpeechSynthesisUtterance(cleanText));
                        });
                    }
                } else {
                    transOutput.innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
                }
            } catch (err) {
                transOutput.innerHTML = '<div class="alert alert-danger">Translation error. Please try again.</div>';
            }
        });
    }

    // -------------------------------------------------------------------
    // 6. EMERGENCY DIRECTORY
    // -------------------------------------------------------------------
    const emCountrySelect = document.getElementById("emCountrySelect");
    const emStateSelect = document.getElementById("emStateSelect");
    const emOutput = document.getElementById("emergencyOutput");
    let locationData = {};

    async function initEmergencyDropdowns() {
        if (!emCountrySelect || !emStateSelect) return;
        try {
            const res = await fetch("/api/emergency/locations");
            const result = await res.json();
            if (result.status === "success") {
                locationData = result.data;
                emCountrySelect.innerHTML = "";
                
                Object.keys(locationData).forEach(country => {
                    const opt = document.createElement("option");
                    opt.value = country;
                    opt.textContent = country;
                    if (country === "India") opt.selected = true;
                    emCountrySelect.appendChild(opt);
                });

                updateStateDropdown();
            }
        } catch (err) {
            console.error("Failed to load emergency location list", err);
        }
    }

    function updateStateDropdown() {
        if (!emCountrySelect || !emStateSelect) return;
        const selectedCountry = emCountrySelect.value;
        const states = locationData[selectedCountry] || [];
        emStateSelect.innerHTML = "";

        states.forEach(state => {
            const opt = document.createElement("option");
            opt.value = state;
            opt.textContent = state;
            if (state.includes("Hyderabad")) opt.selected = true;
            emStateSelect.appendChild(opt);
        });

        loadEmergencyContacts();
    }

    async function loadEmergencyContacts() {
        if (!emCountrySelect || !emStateSelect || !emOutput) return;
        const country = emCountrySelect.value;
        const state = emStateSelect.value;
        if (!country || !state) return;

        try {
            const res = await fetch(`/api/emergency?country=${encodeURIComponent(country)}&state=${encodeURIComponent(state)}`);
            const json = await res.json();

            if (json.status === "success") {
                const c = json.data.contacts;
                emOutput.innerHTML = `
                    <div class="row g-3 my-2">
                        <div class="col-6 col-md-3">
                            <div class="p-3 bg-light rounded text-center border">
                                <i class="bi bi-shield-fill text-danger fs-3"></i>
                                <div class="small text-muted mt-1">Police</div>
                                <div class="fw-bold fs-5 text-danger">${c.police || '112'}</div>
                            </div>
                        </div>
                        <div class="col-6 col-md-3">
                            <div class="p-3 bg-light rounded text-center border">
                                <i class="bi bi-hospital-fill text-danger fs-3"></i>
                                <div class="small text-muted mt-1">Ambulance</div>
                                <div class="fw-bold fs-5 text-danger">${c.ambulance || '108'}</div>
                            </div>
                        </div>
                        <div class="col-6 col-md-3">
                            <div class="p-3 bg-light rounded text-center border">
                                <i class="bi bi-fire text-danger fs-3"></i>
                                <div class="small text-muted mt-1">Fire Service</div>
                                <div class="fw-bold fs-5 text-danger">${c.fire || '101'}</div>
                            </div>
                        </div>
                        <div class="col-6 col-md-3">
                            <div class="p-3 bg-light rounded text-center border">
                                <i class="bi bi-headset text-danger fs-3"></i>
                                <div class="small text-muted mt-1">Tourist Line</div>
                                <div class="fw-bold fs-5 text-danger">${c.tourist_helpline || '1363'}</div>
                            </div>
                        </div>
                    </div>
                    ${c.safety_note ? `
                    <div class="p-3 bg-light rounded border-start border-danger border-4 mt-3">
                        <h6 class="fw-bold text-danger mb-1"><i class="bi bi-info-circle me-1"></i>Regional Safety Advisory</h6>
                        <p class="m-0 small text-dark">${c.safety_note}</p>
                    </div>` : ''}
                `;
            }
        } catch (err) {
            emOutput.innerHTML = '<div class="alert alert-danger">Error loading emergency directory.</div>';
        }
    }

    if (emCountrySelect && emStateSelect) {
        emCountrySelect.addEventListener("change", updateStateDropdown);
        emStateSelect.addEventListener("change", loadEmergencyContacts);
        initEmergencyDropdowns();
    }
});