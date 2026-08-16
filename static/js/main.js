/* TravelMate AI — Frontend Logic Manager */

document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------------
    // 0. MULTILINGUAL UI LOCALIZATION ENGINE
    // -------------------------------------------------------------------
    const globalLangSelect = document.getElementById("globalLangSelect");
    let currentLang = globalLangSelect ? globalLangSelect.value : "en";

    function applyLanguage(lang) {
        currentLang = lang;
        if (typeof UI_TRANSLATIONS === "undefined") return;

        const dict = UI_TRANSLATIONS[lang] || UI_TRANSLATIONS["en"];
        if (!dict) return;

        // Update inner text for all data-i18n elements
        document.querySelectorAll("[data-i18n]").forEach((el) => {
            const key = el.getAttribute("data-i18n");
            if (dict[key]) {
                el.textContent = dict[key];
            }
        });

        // Update input placeholders for all data-i18n-placeholder elements
        document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
            const key = el.getAttribute("data-i18n-placeholder");
            if (dict[key]) {
                el.placeholder = dict[key];
            }
        });
    }

    if (globalLangSelect) {
        globalLangSelect.addEventListener("change", (e) => {
            applyLanguage(e.target.value);
        });
        // Initial application on load
        applyLanguage(currentLang);
    }

    // -------------------------------------------------------------------
    // MARKDOWN FORMATTER (Headings, Dividers, Bold, Italics, Lists)
    // -------------------------------------------------------------------
    function formatMarkdown(text) {
        if (!text) return "";
        return text
            // Horizontal dividers: ---, ___, ***
            .replace(/^(?:---|___|\*\*\*)$/gm, '<hr class="my-3 border-secondary-subtle">')
            // Headings: ###, ##, #
            .replace(/^### (.*$)/gm, '<h6 class="fw-bold text-primary mt-3 mb-2">$1</h6>')
            .replace(/^## (.*$)/gm, '<h5 class="fw-bold text-primary mt-3 mb-2">$1</h5>')
            .replace(/^# (.*$)/gm, '<h4 class="fw-bold text-primary mt-3 mb-2">$1</h4>')
            // Bold: **text** -> <strong>text</strong>
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Italics: *text* -> <em>text</em>
            .replace(/(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)/g, '<em>$1</em>')
            // Bullet points: * text or - text
            .replace(/^\s*[\*\-]\s+(.*)$/gm, '<li class="ms-3 mb-1">$1</li>')
            // Convert plain newlines to line breaks
            .replace(/\n{2,}/g, '<br><br>')
            .replace(/\n/g, '<br>');
    }

    // -------------------------------------------------------------------
    // 1. CHAT ASSISTANT HANDLER
    // -------------------------------------------------------------------
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");
    const chatWindow = document.getElementById("chatWindow");

    if (chatForm && chatInput && chatWindow) {
        chatForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const msg = chatInput.value.trim();
            if (!msg) return;

            // Append user bubble
            appendChatBubble(msg, "user");
            chatInput.value = "";

            // Append loading placeholder
            const loadingBubble = appendChatBubble("Thinking...", "bot");

            try {
                const res = await fetch("/api/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: msg, lang: currentLang })
                });
                const data = await res.json();
                
                if (data.status === "success") {
                    loadingBubble.innerHTML = formatMarkdown(data.reply);
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
    // 2. RECOMMENDATION ENGINE HANDLER
    // -------------------------------------------------------------------
    const recForm = document.getElementById("recommendationForm");
    const recOutput = document.getElementById("recommendationsOutput");

    if (recForm && recOutput) {
        recForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            recOutput.innerHTML = '<div class="text-center p-4"><div class="spinner-border text-primary" role="status"></div></div>';

            const interests = Array.from(document.querySelectorAll(".rec-interest:checked")).map(cb => cb.value);

            const payload = {
                destination: document.getElementById("recDestination").value,
                traveller_type: document.getElementById("recTravellerType").value,
                budget_level: document.getElementById("recBudget").value,
                interests: interests,
                lang: currentLang
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
                    let cardsHtml = `<div class="card p-3 mb-3 bg-light border-0"><h6 class="fw-bold text-primary mb-2">AI Expert Insights</h6><p class="m-0">${formatMarkdown(data.data.ai_insights)}</p></div>`;
                    
                    cardsHtml += '<div class="row g-3">';
                    recs.forEach(item => {
                        cardsHtml += `
                            <div class="col-md-6">
                                <div class="card feature-card h-100 p-3">
                                    <div class="d-flex justify-content-between align-items-start mb-2">
                                        <h6 class="fw-bold m-0">${item.name}</h6>
                                        <span class="score-badge small">Match: ${(item.match_score * 100).toFixed(0)}%</span>
                                    </div>
                                    <p class="text-muted small mb-2">${item.description}</p>
                                    <div class="mt-auto d-flex justify-content-between small text-secondary">
                                        <span><i class="bi bi-tag me-1"></i>${item.category}</span>
                                        <span><i class="bi bi-cash me-1"></i>₹${item.approximate_cost_inr || 'Free'}</span>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    cardsHtml += '</div>';
                    recOutput.innerHTML = cardsHtml;
                } else {
                    recOutput.innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
                }
            } catch (err) {
                recOutput.innerHTML = '<div class="alert alert-danger">Failed to connect to recommendation service.</div>';
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
                traveller_type: document.getElementById("itinStyle").value,
                lang: currentLang
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
                        <div class="card feature-card p-4">
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
            formData.append("target_lang", currentLang);
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
                        <div class="card feature-card p-4">
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
    // 5. TRANSLATOR HANDLER (CHIPS, SPEECH-TO-TEXT & AUDIO TTS)
    // -------------------------------------------------------------------
    const transForm = document.getElementById("translateForm");
    const transText = document.getElementById("transText");
    const transOutput = document.getElementById("translateOutput");
    const transTargetLang = document.getElementById("transTargetLang");
    const transMicBtn = document.getElementById("transMicBtn");

    // 1-Tap Quick Phrase Chips
    document.querySelectorAll(".quick-phrase-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            if (transText) {
                transText.value = chip.getAttribute("data-phrase");
                transForm.dispatchEvent(new Event("submit"));
            }
        });
    });

    // Voice Input (Speech Recognition)
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

            const selectedLang = transTargetLang ? transTargetLang.value : currentLang;

            transOutput.innerHTML = '<div class="text-center p-3"><div class="spinner-border text-primary" role="status"></div></div>';

            try {
                const res = await fetch("/api/translate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        text: textToTranslate,
                        target_lang: selectedLang,
                        destination: "Global / Any Destination"
                    })
                });
                const data = await res.json();

                if (data.status === "success") {
                    const rawText = data.data.translation_data || "";
                    
                    transOutput.innerHTML = `
                        <div class="card feature-card p-4">
                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <h6 class="fw-bold text-primary m-0"><i class="bi bi-check2-circle me-1"></i>Translation Result (${data.data.target_language})</h6>
                                <button class="btn btn-sm btn-outline-primary" id="playAudioBtn">
                                    <i class="bi bi-volume-up-fill me-1"></i>Listen (TTS)
                                </button>
                            </div>
                            <div class="fs-6">${formatMarkdown(rawText)}</div>
                        </div>
                    `;

                    // Audio Text-to-Speech button
                    const playBtn = document.getElementById("playAudioBtn");
                    if (playBtn && 'speechSynthesis' in window) {
                        playBtn.addEventListener("click", () => {
                            const utterance = new SpeechSynthesisUtterance(rawText.replace(/[*#]/g, ''));
                            window.speechSynthesis.speak(utterance);
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
    // 6. EMERGENCY DIRECTORY (INSTANT DYNAMIC DROPDOWNS & LOCAL CACHING)
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