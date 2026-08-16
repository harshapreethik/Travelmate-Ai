/* TravelMate AI — Frontend Logic Manager */

document.addEventListener("DOMContentLoaded", () => {
    let tripCart = [];

    // -------------------------------------------------------------------
    // 0. CLICKABLE SUGGESTION PILLS
    // -------------------------------------------------------------------
    const chatInput = document.getElementById("chatInput");
    const chatForm = document.getElementById("chatForm");

    document.querySelectorAll(".suggestion-pill[data-prompt]").forEach(pill => {
        pill.addEventListener("click", () => {
            if (chatInput && chatForm) {
                chatInput.value = pill.getAttribute("data-prompt");
                chatForm.dispatchEvent(new Event("submit"));
            }
        });
    });

    // -------------------------------------------------------------------
    // MARKDOWN FORMATTER
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
    // 1. CHAT ASSISTANT HANDLER
    // -------------------------------------------------------------------
    const chatWindow = document.getElementById("chatWindow");

    if (chatForm && chatInput && chatWindow) {
        chatForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const msg = chatInput.value.trim();
            if (!msg) return;

            appendChatBubble(msg, "user");
            chatInput.value = "";

            const loadingBubble = appendChatBubble("Thinking...", "bot");
            loadingBubble.innerHTML = '<span class="spinner-grow spinner-grow-sm me-2 text-primary" role="status"></span>Thinking...';

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
                loadingBubble.textContent = "Connection error. Please check server logs.";
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
    // 2. PLACES / RECOMMENDATIONS & DISMISSIBLE TRIP CART
    // -------------------------------------------------------------------
    const recForm = document.getElementById("recommendationForm");
    const recOutput = document.getElementById("recommendationsOutput");
    const recSlider = document.getElementById("recBudgetSlider");
    const recInput = document.getElementById("recBudgetInput");
    const recDisplay = document.getElementById("recBudgetDisplay");
    const cartCountBadge = document.getElementById("cartCountBadge");
    const floatingCartBar = document.getElementById("floatingCartBar");
    const floatingCartCount = document.getElementById("floatingCartCount");
    const floatingCartItems = document.getElementById("floatingCartItems");
    const floatingCheckoutBtn = document.getElementById("floatingCheckoutBtn");
    const floatingDismissBtn = document.getElementById("floatingDismissBtn");

    if (recSlider && recInput) {
        function updateRecBudget(val) {
            let num = parseInt(val) || 0;
            if (recDisplay) recDisplay.textContent = num === 0 ? "Free Entry Only" : `₹${num.toLocaleString("en-IN")}`;
        }
        recSlider.addEventListener("input", (e) => {
            recInput.value = e.target.value;
            updateRecBudget(e.target.value);
        });
        recInput.addEventListener("input", (e) => {
            recSlider.value = e.target.value;
            updateRecBudget(e.target.value);
        });
    }

    function isPlacesTabActive() {
        const recsPane = document.getElementById("recs-pane");
        return recsPane && recsPane.classList.contains("active");
    }

    function updateCartUI(forceHideFloating = false) {
        const count = tripCart.length;

        // Nav Tab Badge
        if (cartCountBadge) {
            if (count > 0) {
                cartCountBadge.textContent = count;
                cartCountBadge.classList.remove("d-none");
            } else {
                cartCountBadge.classList.add("d-none");
            }
        }

        // Floating Cart Bar (Only shows when on Places tab and not dismissed)
        if (floatingCartBar) {
            if (count > 0 && isPlacesTabActive() && !forceHideFloating) {
                floatingCartBar.classList.remove("d-none");
                floatingCartBar.classList.add("d-flex");
                if (floatingCartCount) floatingCartCount.textContent = count;
                if (floatingCartItems) floatingCartItems.textContent = tripCart.join(" • ");
            } else {
                floatingCartBar.classList.add("d-none");
                floatingCartBar.classList.remove("d-flex");
            }
        }

        renderCartInItinerary();
    }

    // Dismiss floating bar manually
    if (floatingDismissBtn) {
        floatingDismissBtn.addEventListener("click", () => {
            if (floatingCartBar) {
                floatingCartBar.classList.add("d-none");
                floatingCartBar.classList.remove("d-flex");
            }
        });
    }

    // Hide floating bar when tab changes
    document.querySelectorAll('#travelTab button[data-bs-toggle="tab"]').forEach(tabBtn => {
        tabBtn.addEventListener('shown.bs.tab', (e) => {
            if (e.target.id !== "recs-tab") {
                if (floatingCartBar) {
                    floatingCartBar.classList.add("d-none");
                    floatingCartBar.classList.remove("d-flex");
                }
            } else {
                updateCartUI();
            }
        });
    });

    if (floatingCheckoutBtn) {
        floatingCheckoutBtn.addEventListener("click", () => {
            const itinTab = document.getElementById("itin-tab");
            if (itinTab) {
                const tabInstance = new bootstrap.Tab(itinTab);
                tabInstance.show();
            }
            if (floatingCartBar) {
                floatingCartBar.classList.add("d-none");
                floatingCartBar.classList.remove("d-flex");
            }
        });
    }

    if (recForm && recOutput) {
        recForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            recOutput.innerHTML = `
                <div class="text-center p-5">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="mt-2 text-muted fw-semibold">Discovering places & curated spots...</p>
                </div>
            `;

            const destination = document.getElementById("recDestination").value.trim();
            const interests = Array.from(document.querySelectorAll(".rec-interest:checked")).map(cb => cb.value);
            const customInterests = document.getElementById("recCustomInterests") ? document.getElementById("recCustomInterests").value.trim() : "";
            const maxBudget = recInput ? `Under ₹${recInput.value}` : "Moderate";

            // Sync destination to itinerary automatically
            const itinDestInput = document.getElementById("itinDestination");
            if (itinDestInput) itinDestInput.value = destination;

            const payload = {
                destination: destination,
                traveller_type: document.getElementById("recTravellerType").value,
                budget_level: maxBudget,
                interests: interests,
                custom_interests: customInterests
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
                    const summary = data.data.destination_summary || `${destination}`;

                    let outputHtml = `
                        <div class="d-flex justify-content-between align-items-center mb-3 px-1">
                            <div>
                                <span class="badge bg-dark px-3 py-2 text-uppercase letter-spacing-1">${summary}</span>
                            </div>
                            <span class="text-muted small fw-semibold">${recs.length} places curated</span>
                        </div>
                        <div class="row g-3">
                    `;

                    recs.forEach(item => {
                        const mapQuery = encodeURIComponent(`${item.name}, ${destination}`);
                        const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${mapQuery}`;
                        const rating = item.rating || 4.8;
                        const reviews = item.reviews_count || "5.2k";
                        const inCart = tripCart.includes(item.name);

                        outputHtml += `
                            <div class="col-md-6">
                                <div class="card h-100 p-3 shadow-sm border-0 rounded-3 d-flex flex-column justify-content-between">
                                    <div>
                                        <div class="d-flex justify-content-between align-items-start mb-1">
                                            <h6 class="fw-bold text-dark m-0 fs-6">${item.name}</h6>
                                            <span class="badge bg-success-subtle text-success border border-success-subtle px-2 py-1 small">
                                                ${item.match_score || 95}% Match
                                            </span>
                                        </div>

                                        <div class="d-flex align-items-center gap-2 mb-2 text-muted small">
                                            <span class="text-warning fw-bold"><i class="bi bi-star-fill me-1"></i>${rating}</span>
                                            <span class="text-muted">(${reviews})</span>
                                            <span>•</span>
                                            <span class="badge bg-light text-secondary border">${item.category}</span>
                                        </div>

                                        <p class="text-dark small mb-3">${item.highlight || ''}</p>

                                        <div class="row g-2 mb-3">
                                            <div class="col-6">
                                                <div class="p-2 bg-light rounded text-center small">
                                                    <span class="text-muted d-block" style="font-size: 0.75rem;">ESTIMATED COST</span>
                                                    <strong class="text-primary">${item.approx_cost || 'Free Entry'}</strong>
                                                </div>
                                            </div>
                                            <div class="col-6">
                                                <div class="p-2 bg-light rounded text-center small">
                                                    <span class="text-muted d-block" style="font-size: 0.75rem;">IDEAL DURATION</span>
                                                    <strong class="text-dark">${item.duration || '2 hrs'}</strong>
                                                </div>
                                            </div>
                                        </div>

                                        ${item.local_tip ? `
                                            <div class="p-2 rounded bg-light border-start border-3 border-warning small text-secondary mb-3">
                                                <strong class="text-dark"><i class="bi bi-shield-check text-warning me-1"></i>Tip:</strong> ${item.local_tip}
                                            </div>
                                        ` : ''}
                                    </div>

                                    <div class="pt-2 border-top d-flex gap-2">
                                        <button type="button" class="btn btn-sm ${inCart ? 'btn-success' : 'btn-outline-dark'} w-50 add-cart-btn" data-name="${item.name}">
                                            <i class="bi ${inCart ? 'bi-check-lg' : 'bi-plus-lg'} me-1"></i>${inCart ? 'Selected' : 'Add to Plan'}
                                        </button>
                                        <a href="${mapsUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-outline-primary w-50 fw-semibold">
                                            <i class="bi bi-geo-alt-fill me-1"></i>Directions
                                        </a>
                                    </div>
                                </div>
                            </div>
                        `;
                    });

                    outputHtml += '</div>';
                    recOutput.innerHTML = outputHtml;

                    // Click listeners for Add to Plan
                    document.querySelectorAll(".add-cart-btn").forEach(btn => {
                        btn.addEventListener("click", () => {
                            const place = btn.getAttribute("data-name");
                            if (tripCart.includes(place)) {
                                tripCart = tripCart.filter(p => p !== place);
                                btn.className = "btn btn-sm btn-outline-dark w-50 add-cart-btn";
                                btn.innerHTML = '<i class="bi bi-plus-lg me-1"></i>Add to Plan';
                            } else {
                                tripCart.push(place);
                                btn.className = "btn btn-sm btn-success w-50 add-cart-btn";
                                btn.innerHTML = '<i class="bi bi-check-lg me-1"></i>Selected';
                            }
                            updateCartUI();
                        });
                    });

                } else {
                    recOutput.innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
                }
            } catch (err) {
                recOutput.innerHTML = '<div class="alert alert-danger">Failed to load places.</div>';
            }
        });
    }

    // -------------------------------------------------------------------
    // 3. ITINERARY BUILDER
    // -------------------------------------------------------------------
    const budgetSlider = document.getElementById("itinBudgetSlider");
    const budgetInput = document.getElementById("itinBudgetInput");
    const budgetDisplay = document.getElementById("budgetDisplay");
    const itinForm = document.getElementById("itineraryForm");
    const itinOutput = document.getElementById("itineraryOutput");
    const cartTrayContainer = document.getElementById("cartTrayContainer");
    const cartBadges = document.getElementById("cartBadges");
    const clearCartBtn = document.getElementById("clearCartBtn");

    function renderCartInItinerary() {
        if (!cartTrayContainer || !cartBadges) return;

        if (tripCart.length > 0) {
            cartTrayContainer.classList.remove("d-none");
            cartBadges.innerHTML = "";
            tripCart.forEach(place => {
                const badge = document.createElement("span");
                badge.className = "badge bg-dark text-white px-2 py-1";
                badge.innerHTML = `${place} <i class="bi bi-x-circle ms-1 cursor-pointer" data-remove="${place}"></i>`;
                cartBadges.appendChild(badge);
            });

            cartBadges.querySelectorAll("[data-remove]").forEach(xBtn => {
                xBtn.addEventListener("click", () => {
                    const toRemove = xBtn.getAttribute("data-remove");
                    tripCart = tripCart.filter(p => p !== toRemove);
                    updateCartUI();
                });
            });
        } else {
            cartTrayContainer.classList.add("d-none");
        }
    }

    if (clearCartBtn) {
        clearCartBtn.addEventListener("click", () => {
            tripCart = [];
            updateCartUI();
        });
    }

    function updateBudgetTier(val) {
        let num = parseInt(val) || 0;
        let tier = "Budget";

        if (num > 15000) {
            tier = "Luxury";
        } else if (num >= 4000) {
            tier = "Comfort";
        }

        if (budgetDisplay) {
            budgetDisplay.textContent = `₹${num.toLocaleString("en-IN")} (${tier})`;
        }
    }

    if (budgetSlider && budgetInput) {
        budgetSlider.addEventListener("input", (e) => {
            budgetInput.value = e.target.value;
            updateBudgetTier(e.target.value);
        });

        budgetInput.addEventListener("input", (e) => {
            budgetSlider.value = e.target.value;
            updateBudgetTier(e.target.value);
        });

        updateBudgetTier(budgetSlider.value);
    }

    if (itinForm && itinOutput) {
        itinForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            itinOutput.innerHTML = `
                <div class="text-center p-5">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="mt-2 text-muted fw-semibold">Structuring daily timeline & dining schedule...</p>
                </div>
            `;

            const destination = document.getElementById("itinDestination").value.trim();
            const numDays = parseInt(document.getElementById("itinDays").value);
            const budgetAmount = budgetInput ? `₹${budgetInput.value}` : "₹5,000";
            const travellerType = document.getElementById("itinStyle").value;
            const customSchedule = document.getElementById("itinCustomSchedule") ? document.getElementById("itinCustomSchedule").value.trim() : "";

            const payload = {
                destination: destination,
                num_days: numDays,
                budget_level: budgetAmount,
                traveller_type: travellerType,
                selected_places: tripCart,
                custom_schedule: customSchedule
            };

            try {
                const res = await fetch("/api/itinerary", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();

                if (data.status === "success") {
                    const plan = data.data;
                    const days = plan.days || [];

                    let outputHtml = `
                        <div class="card p-3 mb-4 border-0 shadow-sm bg-dark text-white rounded-3">
                            <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
                                <div>
                                    <h5 class="fw-bold m-0"><i class="bi bi-geo-alt-fill text-primary me-2"></i>${plan.num_days}-Day Trip to ${plan.destination}</h5>
                                    <small class="text-white-50">${plan.budget_level} Budget • ${travellerType}</small>
                                </div>
                                <div class="text-end">
                                    <span class="badge bg-primary px-3 py-2 fs-6"><i class="bi bi-wallet2 me-1"></i>${plan.estimated_daily_budget || 'Budget Planned'}</span>
                                </div>
                            </div>
                            ${plan.transit_summary ? `
                                <div class="mt-2 pt-2 border-top border-secondary small text-white-50">
                                    <i class="bi bi-compass me-1 text-primary"></i><strong>Transit Advice:</strong> ${plan.transit_summary}
                                </div>
                            ` : ''}
                        </div>
                    `;

                    days.forEach(d => {
                        outputHtml += `
                            <div class="card p-4 mb-4 shadow-sm border-0 rounded-3">
                                <div class="d-flex justify-content-between align-items-center pb-2 mb-3 border-bottom">
                                    <h6 class="fw-bold text-primary m-0 fs-5">
                                        <i class="bi bi-calendar-event me-2"></i>Day ${d.day_number}: ${d.theme}
                                    </h6>
                                    <span class="badge bg-light text-secondary border">Full Day Plan</span>
                                </div>

                                <!-- Schedule Timeline -->
                                <div class="timeline ps-2 mb-4">
                                    <div class="mb-3 ps-3 border-start border-3 border-warning position-relative">
                                        <div class="d-flex justify-content-between align-items-start mb-1">
                                            <strong class="text-dark"><i class="bi bi-sunrise-fill text-warning me-2"></i>Morning</strong>
                                            <span class="badge bg-light text-secondary border small">${d.morning.duration || '3 hrs'}</span>
                                        </div>
                                        <div class="fw-semibold text-primary small">${d.morning.activity}</div>
                                        <p class="text-muted small m-0">${d.morning.description}</p>
                                    </div>

                                    <div class="mb-3 ps-3 border-start border-3 border-primary position-relative">
                                        <div class="d-flex justify-content-between align-items-start mb-1">
                                            <strong class="text-dark"><i class="bi bi-sun-fill text-primary me-2"></i>Afternoon</strong>
                                            <span class="badge bg-light text-secondary border small">${d.afternoon.duration || '2.5 hrs'}</span>
                                        </div>
                                        <div class="fw-semibold text-primary small">${d.afternoon.activity}</div>
                                        <p class="text-muted small m-0">${d.afternoon.description}</p>
                                    </div>

                                    <div class="mb-3 ps-3 border-start border-3 border-info position-relative">
                                        <div class="d-flex justify-content-between align-items-start mb-1">
                                            <strong class="text-dark"><i class="bi bi-moon-stars-fill text-info me-2"></i>Evening</strong>
                                            <span class="badge bg-light text-secondary border small">${d.evening.duration || '3 hrs'}</span>
                                        </div>
                                        <div class="fw-semibold text-primary small">${d.evening.activity}</div>
                                        <p class="text-muted small m-0">${d.evening.description}</p>
                                    </div>
                                </div>

                                <!-- Dining Section -->
                                ${d.dining_plan ? `
                                    <div class="p-3 bg-light rounded-3 border mb-3">
                                        <h6 class="fw-bold text-dark mb-2 small text-uppercase letter-spacing-1">
                                            <i class="bi bi-cup-hot-fill text-danger me-1"></i>Day ${d.day_number} Meals & Dining
                                        </h6>
                                        <div class="row g-2 small">
                                            <div class="col-md-4">
                                                <div class="p-2 bg-white rounded border">
                                                    <span class="text-muted d-block" style="font-size: 0.75rem;">BREAKFAST</span>
                                                    <strong class="text-dark">${d.dining_plan.breakfast || 'Traditional Breakfast'}</strong>
                                                </div>
                                            </div>
                                            <div class="col-md-4">
                                                <div class="p-2 bg-white rounded border">
                                                    <span class="text-muted d-block" style="font-size: 0.75rem;">LUNCH</span>
                                                    <strong class="text-dark">${d.dining_plan.lunch || 'Regional Specialty'}</strong>
                                                </div>
                                            </div>
                                            <div class="col-md-4">
                                                <div class="p-2 bg-white rounded border">
                                                    <span class="text-muted d-block" style="font-size: 0.75rem;">DINNER / STREET FOOD</span>
                                                    <strong class="text-dark">${d.dining_plan.dinner || 'Signature Dinner'}</strong>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ` : ''}

                                ${d.pro_tip ? `
                                    <div class="p-2 bg-light rounded border-start border-warning border-3 small">
                                        <strong class="text-dark"><i class="bi bi-lightbulb-fill text-warning me-1"></i>Day ${d.day_number} Tip:</strong> ${d.pro_tip}
                                    </div>
                                ` : ''}
                            </div>
                        `;
                    });

                    itinOutput.innerHTML = outputHtml;
                } else {
                    itinOutput.innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
                }
            } catch (err) {
                itinOutput.innerHTML = '<div class="alert alert-danger">Error generating itinerary. Please try again.</div>';
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
                        <div class="card feature-card p-4 shadow-sm border-0 rounded-3">
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
    // 5. TRANSLATOR HANDLER (Auto-Detect, Chips, Speech & TTS)
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
                        <div class="card feature-card p-4 shadow-sm border-0 rounded-3">
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