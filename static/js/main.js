/* TravelMate AI — Frontend Logic Manager */

// ===================================================================
// GLOBAL INTRO OVERLAY HANDLER
// ===================================================================
window.dismissIntro = function () {
    const overlay = document.getElementById("introOverlay");
    if (!overlay) return;
    overlay.classList.remove("intro-ready");
    overlay.classList.add("intro-closing");
    setTimeout(() => {
        overlay.style.display = "none";
        overlay.remove();
    }, 450);
};

document.addEventListener("DOMContentLoaded", () => {
    let tripCart = [];
    
    // In-memory conversation history (Persists until page refresh)
    let chatSessionHistory = [];

    // Trigger smooth intro animation on load
    const introOverlay = document.getElementById("introOverlay");
    if (introOverlay) {
        requestAnimationFrame(() => {
            introOverlay.classList.add("intro-ready");
        });
    }

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
    // MARKDOWN FORMATTER (WITH CLICKABLE MAP LINK PARSING)
    // -------------------------------------------------------------------
    function formatMarkdown(text) {
        if (!text) return "";
        let html = text
            .replace(/^(?:---|___|\*\*\*)$/gm, '<hr class="my-3 border-secondary-subtle">')
            .replace(/^#### (.*$)/gm, '<h6 class="fw-bold text-dark mt-3 mb-1">$1</h6>')
            .replace(/^### (.*$)/gm, '<h5 class="fw-bold text-primary mt-3 mb-2">$1</h5>')
            .replace(/^## (.*$)/gm, '<h4 class="fw-bold text-primary mt-4 mb-2">$1</h4>')
            .replace(/^# (.*$)/gm, '<h3 class="fw-bold text-primary mt-4 mb-3">$1</h3>')
            // Convert [Place Name](URL) into clickable anchor tag
            .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-primary text-decoration-underline fw-semibold"><i class="bi bi-geo-alt-fill text-danger me-1"></i>$1</a>')
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
    function streamTextWordByWord(element, fullText, speed = 15) {
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
    // 1. CHAT ASSISTANT HANDLER (MULTI-TURN MEMORY ENABLED)
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
                    body: JSON.stringify({ 
                        message: msg,
                        history: chatSessionHistory // Send full in-memory history
                    })
                });
                const data = await res.json();

                if (data.status === "success" || data.reply || data.response) {
                    const botReply = data.reply || data.response;
                    
                    // Track this turn in session memory
                    chatSessionHistory.push({ role: "user", text: msg });
                    chatSessionHistory.push({ role: "model", text: botReply });

                    streamTextWordByWord(loadingBubble, botReply, 15);
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

        // Floating Cart Bar
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

    if (floatingDismissBtn) {
        floatingDismissBtn.addEventListener("click", () => {
            if (floatingCartBar) {
                floatingCartBar.classList.add("d-none");
                floatingCartBar.classList.remove("d-flex");
            }
        });
    }

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

    // -------------------------------------------------------------------
    // 3. ITINERARY BUILDER (WITH AUTO-TRIGGER & GOOGLE MAPS ROUTING)
    // -------------------------------------------------------------------
    const budgetSlider = document.getElementById("itinBudgetSlider");
    const budgetInput = document.getElementById("itinBudgetInput");
    const budgetDisplay = document.getElementById("budgetDisplay");
    const itinForm = document.getElementById("itineraryForm");
    const itinOutput = document.getElementById("itineraryOutput");
    const cartTrayContainer = document.getElementById("cartTrayContainer");
    const cartBadges = document.getElementById("cartBadges");
    const clearCartBtn = document.getElementById("clearCartBtn");

    if (floatingCheckoutBtn) {
        floatingCheckoutBtn.addEventListener("click", () => {
            const itinTab = document.getElementById("itin-tab");
            if (itinTab) {
                const tabInstance = bootstrap.Tab.getOrCreateInstance(itinTab);
                tabInstance.show();
            }
            if (floatingCartBar) {
                floatingCartBar.classList.add("d-none");
                floatingCartBar.classList.remove("d-flex");
            }
            if (itinForm) {
                setTimeout(() => {
                    itinForm.dispatchEvent(new Event("submit"));
                }, 150);
            }
        });
    }

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

    if (itinForm && itinOutput) {
        itinForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            itinOutput.innerHTML = `
                <div class="text-center p-5">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="mt-2 text-muted fw-semibold">Structuring daily timeline, Google Maps routes & dining schedule...</p>
                </div>
            `;

            const destination = document.getElementById("itinDestination").value.trim();
            const numDays = parseInt(document.getElementById("itinDays").value) || 2;
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

                if (data.status === "success" && data.data) {
                    const plan = data.data;
                    const days = Array.isArray(plan.days) ? plan.days : [];

                    let outputHtml = `
                        <div class="card p-3 mb-4 border-0 shadow-sm bg-dark text-white rounded-3">
                            <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
                                <div>
                                    <h5 class="fw-bold m-0"><i class="bi bi-geo-alt-fill text-primary me-2"></i>${plan.num_days || numDays}-Day Trip to ${plan.destination || destination}</h5>
                                    <small class="text-white-50">${plan.budget_level || budgetAmount} Budget • ${travellerType}</small>
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

                    days.forEach((d, index) => {
                        const mAct = typeof d.morning === 'object' ? (d.morning?.activity || 'Morning Sightseeing') : (d.morning || 'Morning Sightseeing');
                        const mDesc = typeof d.morning === 'object' ? (d.morning?.description || '') : '';
                        const mDur = typeof d.morning === 'object' ? (d.morning?.duration || '3 hrs') : '3 hrs';

                        const aAct = typeof d.afternoon === 'object' ? (d.afternoon?.activity || 'Afternoon Landmark') : (d.afternoon || 'Afternoon Landmark');
                        const aDesc = typeof d.afternoon === 'object' ? (d.afternoon?.description || '') : '';
                        const aDur = typeof d.afternoon === 'object' ? (d.afternoon?.duration || '2.5 hrs') : '2.5 hrs';

                        const eAct = typeof d.evening === 'object' ? (d.evening?.activity || 'Evening Exploration') : (d.evening || 'Evening Exploration');
                        const eDesc = typeof d.evening === 'object' ? (d.evening?.description || '') : '';
                        const eDur = typeof d.evening === 'object' ? (d.evening?.duration || '3 hrs') : '3 hrs';

                        const bFast = d.dining_plan ? (d.dining_plan.breakfast || 'Traditional Breakfast') : 'Traditional Breakfast';
                        const lunch = d.dining_plan ? (d.dining_plan.lunch || 'Regional Specialty') : 'Regional Specialty';
                        const dinner = d.dining_plan ? (d.dining_plan.dinner || 'Signature Dinner') : 'Signature Dinner';

                        const fullRouteUrl = `https://www.google.com/maps/dir/${encodeURIComponent(mAct + ', ' + destination)}/${encodeURIComponent(aAct + ', ' + destination)}/${encodeURIComponent(eAct + ', ' + destination)}`;
                        const getSingleMapUrl = (act) => `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(act + ', ' + destination)}`;

                        outputHtml += `
                            <div class="card p-4 mb-4 shadow-sm border-0 rounded-3">
                                <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 pb-2 mb-3 border-bottom">
                                    <h6 class="fw-bold text-primary m-0 fs-5">
                                        <i class="bi bi-calendar-event me-2"></i>Day ${d.day_number || (index + 1)}: ${d.theme || 'Exploration'}
                                    </h6>
                                    <a href="${fullRouteUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-outline-primary fw-semibold">
                                        <i class="bi bi-map-fill me-1"></i>Navigate Day ${d.day_number || (index + 1)} on Google Maps
                                    </a>
                                </div>

                                <div class="timeline ps-2 mb-4">
                                    <div class="mb-3 ps-3 border-start border-3 border-warning position-relative">
                                        <div class="d-flex justify-content-between align-items-start mb-1">
                                            <strong class="text-dark"><i class="bi bi-sunrise-fill text-warning me-2"></i>Morning</strong>
                                            <span class="badge bg-light text-secondary border small">${mDur}</span>
                                        </div>
                                        <div class="d-flex justify-content-between align-items-center mb-1">
                                            <div class="fw-semibold text-primary small">${mAct}</div>
                                            <a href="${getSingleMapUrl(mAct)}" target="_blank" rel="noopener noreferrer" class="btn btn-xs btn-outline-secondary py-0 px-2 small" style="font-size: 0.72rem;">
                                                <i class="bi bi-geo-alt-fill text-danger me-1"></i>Google Maps
                                            </a>
                                        </div>
                                        <p class="text-muted small m-0">${mDesc}</p>
                                    </div>

                                    <div class="mb-3 ps-3 border-start border-3 border-primary position-relative">
                                        <div class="d-flex justify-content-between align-items-start mb-1">
                                            <strong class="text-dark"><i class="bi bi-sun-fill text-primary me-2"></i>Afternoon</strong>
                                            <span class="badge bg-light text-secondary border small">${aDur}</span>
                                        </div>
                                        <div class="d-flex justify-content-between align-items-center mb-1">
                                            <div class="fw-semibold text-primary small">${aAct}</div>
                                            <a href="${getSingleMapUrl(aAct)}" target="_blank" rel="noopener noreferrer" class="btn btn-xs btn-outline-secondary py-0 px-2 small" style="font-size: 0.72rem;">
                                                <i class="bi bi-geo-alt-fill text-danger me-1"></i>Google Maps
                                            </a>
                                        </div>
                                        <p class="text-muted small m-0">${aDesc}</p>
                                    </div>

                                    <div class="mb-3 ps-3 border-start border-3 border-info position-relative">
                                        <div class="d-flex justify-content-between align-items-start mb-1">
                                            <strong class="text-dark"><i class="bi bi-moon-stars-fill text-info me-2"></i>Evening</strong>
                                            <span class="badge bg-light text-secondary border small">${eDur}</span>
                                        </div>
                                        <div class="d-flex justify-content-between align-items-center mb-1">
                                            <div class="fw-semibold text-primary small">${eAct}</div>
                                            <a href="${getSingleMapUrl(eAct)}" target="_blank" rel="noopener noreferrer" class="btn btn-xs btn-outline-secondary py-0 px-2 small" style="font-size: 0.72rem;">
                                                <i class="bi bi-geo-alt-fill text-danger me-1"></i>Google Maps
                                            </a>
                                        </div>
                                        <p class="text-muted small m-0">${eDesc}</p>
                                    </div>
                                </div>

                                <div class="p-3 bg-light rounded-3 border mb-3">
                                    <h6 class="fw-bold text-dark mb-2 small text-uppercase letter-spacing-1">
                                        <i class="bi bi-cup-hot-fill text-danger me-1"></i>Day ${d.day_number || (index + 1)} Meals & Dining
                                    </h6>
                                    <div class="row g-2 small">
                                        <div class="col-md-4">
                                            <div class="p-2 bg-white rounded border h-100">
                                                <span class="text-muted d-block" style="font-size: 0.75rem;">BREAKFAST</span>
                                                <strong class="text-dark">${bFast}</strong>
                                            </div>
                                        </div>
                                        <div class="col-md-4">
                                            <div class="p-2 bg-white rounded border h-100">
                                                <span class="text-muted d-block" style="font-size: 0.75rem;">LUNCH</span>
                                                <strong class="text-dark">${lunch}</strong>
                                            </div>
                                        </div>
                                        <div class="col-md-4">
                                            <div class="p-2 bg-white rounded border h-100">
                                                <span class="text-muted d-block" style="font-size: 0.75rem;">DINNER / STREET FOOD</span>
                                                <strong class="text-dark">${dinner}</strong>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                ${d.pro_tip ? `
                                    <div class="p-2 bg-light rounded border-start border-warning border-3 small">
                                        <strong class="text-dark"><i class="bi bi-lightbulb-fill text-warning me-1"></i>Tip:</strong> ${d.pro_tip}
                                    </div>
                                ` : ''}
                            </div>
                        `;
                    });

                    itinOutput.innerHTML = outputHtml;
                } else {
                    itinOutput.innerHTML = `<div class="alert alert-warning">${data.message || 'Unable to build plan.'}</div>`;
                }
            } catch (err) {
                console.error("Itinerary render error:", err);
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
    const visionTargetLang = document.getElementById("visionTargetLang");

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

            const targetLang = visionTargetLang ? visionTargetLang.value : "English";

            visionOutput.innerHTML = '<div class="text-center p-4"><div class="spinner-border text-primary" role="status"></div><p class="mt-2 text-muted">Analyzing image and translating text...</p></div>';

            const formData = new FormData();
            formData.append("file", file);
            formData.append("destination", "Global / Any Destination");
            formData.append("target_lang", targetLang);
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
                            <h6 class="fw-bold text-primary mb-3"><i class="bi bi-eye me-2"></i>Visual Analysis Result (${targetLang})</h6>
                            <div>${formatMarkdown(data.analysis)}</div>
                        </div>
                    `;
                } else {
                    visionOutput.innerHTML = `<div class="alert alert-warning">${data.message || 'Failed to process image.'}</div>`;
                }
            } catch (err) {
                visionOutput.innerHTML = '<div class="alert alert-danger">Error processing image.</div>';
            }
        });
    }

    // -------------------------------------------------------------------
    // 5. TRANSLATOR HANDLER (CONTINUOUS STREAMING VOICE & MANUAL SUBMIT)
    // -------------------------------------------------------------------
    const transForm = document.getElementById("translateForm");
    const transText = document.getElementById("transText");
    const transOutput = document.getElementById("translateOutput");
    const transMicBtn = document.getElementById("transMicBtn");
    const transSourceLang = document.getElementById("transSourceLang");
    const transTargetLang = document.getElementById("transTargetLang");
    const swapLangBtn = document.getElementById("swapLangBtn");

    if (swapLangBtn && transSourceLang && transTargetLang) {
        swapLangBtn.addEventListener("click", () => {
            if (transSourceLang.value !== "auto") {
                const temp = transSourceLang.value;
                transSourceLang.value = transTargetLang.value;
                transTargetLang.value = temp;
            }
        });
    }

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
        
        // Continuous listening for full natural sentences
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        let isListening = false;
        let silenceTimer = null;
        let finalTranscript = "";

        function resetSilenceTimer() {
            clearTimeout(silenceTimer);
            // Auto-stop after 3 full seconds of total silence
            silenceTimer = setTimeout(() => {
                if (isListening) {
                    recognition.stop();
                }
            }, 3000);
        }

        transMicBtn.addEventListener("click", () => {
            if (!isListening) {
                finalTranscript = transText.value ? transText.value + " " : "";
                try {
                    recognition.start();
                    isListening = true;
                    transMicBtn.classList.add("btn-danger");
                    transMicBtn.setAttribute("title", "Listening... Click to stop");
                    resetSilenceTimer();
                } catch (e) {
                    console.warn("Recognition already active:", e);
                }
            } else {
                recognition.stop();
            }
        });

        recognition.onresult = (event) => {
            resetSilenceTimer();
            let interimTranscript = "";

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript + " ";
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            transText.value = (finalTranscript + interimTranscript).trim();
            transText.focus();
        };

        recognition.onerror = (event) => {
            console.warn("Speech recognition error:", event.error);
            clearTimeout(silenceTimer);
            isListening = false;
            transMicBtn.classList.remove("btn-danger");
        };

        recognition.onend = () => {
            clearTimeout(silenceTimer);
            isListening = false;
            transMicBtn.classList.remove("btn-danger");
            transMicBtn.setAttribute("title", "Click to speak");
            transText.focus();
        };
    }

    if (transForm && transOutput) {
        transForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const textToTranslate = transText.value.trim();
            if (!textToTranslate) return;

            const targetLang = transTargetLang ? transTargetLang.value : "Telugu";
            const sourceLang = transSourceLang ? transSourceLang.value : "auto";

            transOutput.innerHTML = `
                <div class="text-center p-3">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="small text-muted mt-2">Translating to ${targetLang} with phonetics...</p>
                </div>
            `;

            try {
                const res = await fetch("/api/translate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        text: textToTranslate,
                        target_lang: targetLang,
                        source_lang: sourceLang,
                        destination: "Global"
                    })
                });
                const data = await res.json();

                if (data.status === "success") {
                    const rawText = (data.data && data.data.translation_data) ? data.data.translation_data : (typeof data.data === 'string' ? data.data : "");
                    
                    transOutput.innerHTML = `
                        <div class="card feature-card p-4 shadow-sm border-0 rounded-3">
                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <h6 class="fw-bold text-primary m-0"><i class="bi bi-translate me-2"></i>Translation (${targetLang})</h6>
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
                            const cleanText = rawText.replace(/[*#_`]/g, '');
                            window.speechSynthesis.speak(new SpeechSynthesisUtterance(cleanText));
                        });
                    }
                } else {
                    transOutput.innerHTML = `<div class="alert alert-warning">${data.message || 'Translation failed.'}</div>`;
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

    const EMERGENCY_DIRECTORY_DATA = {
        "India": {
            "Telangana (Hyderabad)": [
                { title: "Unified Emergency (Police/Fire/Ambulance)", number: "112", icon: "bi-shield-check", desc: "Centralized all-in-one emergency dispatch" },
                { title: "Hyderabad Police Control Room", number: "100", icon: "bi-shield-fill-exclamation", desc: "Immediate local police assistance" },
                { title: "Ambulance & Trauma Care", number: "108", icon: "bi-hospital", desc: "Free emergency medical ambulance" },
                { title: "Fire & Rescue Service", number: "101", icon: "bi-fire", desc: "Fire emergency and structural rescue" },
                { title: "Telangana She Team (Women Safety)", number: "9490616555", icon: "bi-person-heart", desc: "24/7 women safety & immediate response" },
                { title: "National Tourist Helpline", number: "1363", icon: "bi-headset", desc: "Toll-free multilingual tourist support" },
                { title: "RGIA Airport Police Station", number: "040-27853418", icon: "bi-airplane-fill", desc: "Hyderabad international airport station" }
            ],
            "Andhra Pradesh (Amaravati / Vizag / Guntur)": [
                { title: "AP Unified Emergency", number: "112", icon: "bi-shield-check", desc: "Statewide unified emergency response" },
                { title: "AP Police Control Room", number: "100", icon: "bi-shield-fill-exclamation", desc: "Law enforcement dispatch" },
                { title: "Medical Emergency Ambulance", number: "108", icon: "bi-hospital", desc: "24/7 trauma care and ambulance transport" },
                { title: "Fire Services", number: "101", icon: "bi-fire", desc: "Fire accidents and rescue operations" },
                { title: "Disha SOS Helpline", number: "112", icon: "bi-person-heart", desc: "Dedicated women protection emergency hotline" }
            ],
            "Maharashtra (Mumbai / Pune)": [
                { title: "Maharashtra Emergency Unified", number: "112", icon: "bi-shield-check", desc: "All-in-one emergency helpline" },
                { title: "Mumbai Police Control Room", number: "022-22621855", icon: "bi-shield-fill-exclamation", desc: "Direct Mumbai police dispatch" },
                { title: "Ambulance Services", number: "108", icon: "bi-hospital", desc: "Medical emergencies" },
                { title: "Mumbai Tourist Assistance", number: "022-22845678", icon: "bi-headset", desc: "MTDC tourist assistance desk" }
            ],
            "Delhi (NCR)": [
                { title: "Delhi Central Emergency", number: "112", icon: "bi-shield-check", desc: "Unified police, medical, and fire dispatch" },
                { title: "Delhi Tourist Police", number: "011-23365337", icon: "bi-headset", desc: "Dedicated tourist security & help desk" },
                { title: "Delhi Medical Ambulance (CATS)", number: "102", icon: "bi-hospital", desc: "Centralized ambulance network" }
            ],
            "Karnataka (Bengaluru)": [
                { title: "Bengaluru City Police", number: "112", icon: "bi-shield-check", desc: "Central command & dispatch" },
                { title: "Emergency Ambulance", number: "108", icon: "bi-hospital", desc: "Trauma transport" },
                { title: "Bengaluru Traffic Police Helpline", number: "080-22943030", icon: "bi-car-front", desc: "Traffic clearance & roadside help" }
            ],
            "Tamil Nadu (Chennai)": [
                { title: "Tamil Nadu Emergency Unified", number: "112", icon: "bi-shield-check", desc: "State unified command" },
                { title: "Chennai City Police", number: "100", icon: "bi-shield-fill-exclamation", desc: "Police assistance" },
                { title: "Medical Emergency Ambulance", number: "108", icon: "bi-hospital", desc: "Trauma ambulance dispatch" }
            ]
        },
        "United States": {
            "National (All States / Major Cities)": [
                { title: "Universal Emergency Number", number: "911", icon: "bi-shield-check", desc: "Immediate Police, Fire, and Ambulance dispatch" },
                { title: "Non-Emergency City Services", number: "311", icon: "bi-info-circle-fill", desc: "Non-urgent city services & police records" },
                { title: "National Poison Control Center", number: "1-800-222-1222", icon: "bi-capsule", desc: "24/7 toxic exposure & medical triage" },
                { title: "Crisis & Suicide Lifeline", number: "988", icon: "bi-heart-pulse", desc: "24/7 confidential mental healthcare" }
            ]
        },
        "United Kingdom": {
            "National (London / UK Wide)": [
                { title: "UK Emergency Services", number: "999", icon: "bi-shield-check", desc: "Police, Ambulance, Fire Brigade, Coastguard" },
                { title: "European Emergency Line", number: "112", icon: "bi-shield-check", desc: "Universal European emergency line" },
                { title: "NHS Non-Emergency Health Advice", number: "111", icon: "bi-hospital", desc: "Free medical advice when not a 999 emergency" },
                { title: "Non-Emergency Police Report", number: "101", icon: "bi-shield-fill-exclamation", desc: "Report non-urgent incidents" }
            ]
        },
        "United Arab Emirates": {
            "National (Dubai / Abu Dhabi)": [
                { title: "UAE Police Emergency", number: "999", icon: "bi-shield-check", desc: "Immediate police dispatch" },
                { title: "Ambulance Dispatch", number: "998", icon: "bi-hospital", desc: "Emergency medical transport" },
                { title: "Civil Defence (Fire Rescue)", number: "997", icon: "bi-fire", desc: "Fire accidents & rescue" },
                { title: "Dubai Tourist Police", number: "901", icon: "bi-headset", desc: "Visitor assistance, lost items, and tourist inquiries" }
            ]
        },
        "European Union": {
            "Universal EU Coverage": [
                { title: "Pan-European Universal Emergency", number: "112", icon: "bi-shield-check", desc: "Free emergency connection in all EU countries" }
            ]
        },
        "Japan": {
            "National (Tokyo / Osaka / Kyoto)": [
                { title: "Japan Police Emergency", number: "110", icon: "bi-shield-fill-exclamation", desc: "Immediate police dispatch" },
                { title: "Ambulance & Fire Service", number: "119", icon: "bi-hospital", desc: "Fire fighting and emergency medical transport" },
                { title: "Japan Helpline (English)", number: "0570-000-911", icon: "bi-headset", desc: "24-hour English emergency and consultation line" }
            ]
        }
    };

    function initEmergencySystem() {
        if (!emCountrySelect || !emStateSelect || !emOutput) return;

        emCountrySelect.innerHTML = "";
        Object.keys(EMERGENCY_DIRECTORY_DATA).forEach(country => {
            const opt = document.createElement("option");
            opt.value = country;
            opt.textContent = country;
            if (country === "India") opt.selected = true;
            emCountrySelect.appendChild(opt);
        });

        function updateStates() {
            const country = emCountrySelect.value;
            const states = EMERGENCY_DIRECTORY_DATA[country] || {};
            emStateSelect.innerHTML = "";

            Object.keys(states).forEach(state => {
                const opt = document.createElement("option");
                opt.value = state;
                opt.textContent = state;
                if (state.includes("Hyderabad")) opt.selected = true;
                emStateSelect.appendChild(opt);
            });

            renderHelplineCards();
        }

        function renderHelplineCards() {
            const country = emCountrySelect.value;
            const state = emStateSelect.value;
            const contacts = (EMERGENCY_DIRECTORY_DATA[country] && EMERGENCY_DIRECTORY_DATA[country][state]) || [];

            if (!contacts.length) {
                emOutput.innerHTML = `<div class="p-3 text-muted border rounded bg-light">No records found. Dial universal emergency <strong>112</strong>.</div>`;
                return;
            }

            let html = `
                <div class="card p-3 p-md-4 border shadow-sm rounded-3 mt-3">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h6 class="fw-bold text-dark m-0 d-flex align-items-center">
                            <i class="bi bi-shield-fill-check text-danger me-2"></i>Verified Helplines: ${state}, ${country}
                        </h6>
                        <span class="badge bg-danger-subtle text-danger border border-danger-subtle px-2 py-1 small">Tap to Dial</span>
                    </div>
                    <div class="row g-3">
            `;

            contacts.forEach(item => {
                const cleanPhone = item.number.replace(/[^0-9+]/g, '');

                html += `
                    <div class="col-12 col-md-6">
                        <div class="p-3 border rounded-3 bg-white h-100 d-flex flex-column justify-content-between shadow-xs">
                            <div class="d-flex align-items-start gap-2 mb-2">
                                <i class="bi ${item.icon} text-danger fs-4 mt-1"></i>
                                <div>
                                    <h6 class="fw-bold text-dark m-0">${item.title}</h6>
                                    <small class="text-muted d-block">${item.desc}</small>
                                </div>
                            </div>
                            <div class="pt-2 border-top mt-2 d-flex justify-content-between align-items-center">
                                <span class="fs-5 fw-bold text-dark font-monospace">${item.number}</span>
                                <a href="tel:${cleanPhone}" class="btn btn-danger btn-sm px-3 py-1.5 fw-semibold d-flex align-items-center gap-1 shadow-sm text-decoration-none">
                                    <i class="bi bi-telephone-fill"></i>
                                    <span>Call Now</span>
                                </a>
                            </div>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                    <div class="p-3 bg-light rounded border-start border-danger border-4 mt-4">
                        <h6 class="fw-bold text-danger mb-1"><i class="bi bi-info-circle-fill me-1"></i>Safety Advisory</h6>
                        <p class="m-0 small text-dark">Always keep emergency location sharing active on your phone while traveling. In extreme emergencies with no cellular data, SMS or direct voice calls on unified emergency numbers (112 / 911 / 999) work across any active cellular tower.</p>
                    </div>
                </div>
            `;

            emOutput.innerHTML = html;
        }

        emCountrySelect.addEventListener("change", updateStates);
        emStateSelect.addEventListener("change", renderHelplineCards);

        updateStates();
    }

    if (emCountrySelect && emStateSelect) {
        initEmergencySystem();
    }
});