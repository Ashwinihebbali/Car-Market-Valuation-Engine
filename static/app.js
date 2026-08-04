/* ==========================================================================
   AutoValuate Pro — Enterprise Automotive Valuation Application Logic
   ========================================================================== */

let appMetadata = null;
let chartInstances = {};
let debounceTimer = null;
let currentCurrency = "INR";
let currentPredictionData = null;

document.addEventListener("DOMContentLoaded", () => {
    initTabNavigation();
    loadDashboardData();
});

function setCurrency(curr) {
    currentCurrency = curr;
    document.getElementById("btnINR").classList.toggle("active", curr === "INR");
    document.getElementById("btnUSD").classList.toggle("active", curr === "USD");

    if (currentPredictionData) {
        updatePredictionUI(currentPredictionData);
    }
    
    if (document.getElementById("tab-market").classList.contains("active")) {
        renderMarketCharts();
    }
    if (document.getElementById("tab-compare").classList.contains("active")) {
        runComparison();
    }
}

// Tab Navigation
function initTabNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    const tabPanes = document.querySelectorAll(".tab-pane");

    const titles = {
        "tab-predictor": { title: "Instant Car Price Valuation", subtitle: "Calculate precise market resale values in Indian Rupees (₹ Lakhs) & Global USD" },
        "tab-compare": { title: "Side-by-Side Vehicle Comparison Engine", subtitle: "Compare market values and technical parameters between two vehicle configurations" },
        "tab-market": { title: "Automotive Market Intelligence", subtitle: "Brand valuation rankings, horsepower distributions, and body style statistics" }
    };

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetTab = item.getAttribute("data-tab");
            
            navItems.forEach(i => i.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));

            item.classList.add("active");
            document.getElementById(targetTab).classList.add("active");

            if (titles[targetTab]) {
                document.getElementById("tabTitle").innerText = titles[targetTab].title;
                document.getElementById("tabSubtitle").innerText = titles[targetTab].subtitle;
            }

            if (targetTab === "tab-market") {
                renderMarketCharts();
            } else if (targetTab === "tab-compare") {
                populateCompareSelects();
                runComparison();
            }
        });
    });
}

// Load Metadata & Select Options
async function loadDashboardData() {
    try {
        const res = await fetch("/api/metadata");
        if (!res.ok) throw new Error("Failed to load metadata");
        appMetadata = await res.json();

        populateSelectOptions();
        triggerPredict();
    } catch (err) {
        console.error("Metadata load error:", err);
    }
}

function populateSelectOptions() {
    if (!appMetadata || !appMetadata.categorical_options) return;

    const opts = appMetadata.categorical_options;

    populateSelect("brandSelect", opts.brand, "toyota");
    populateSelect("bodySelect", opts.carbody, "sedan");
    populateSelect("fuelSelect", opts.fueltype, "gas");
    populateSelect("driveSelect", opts.drivewheel, "fwd");
    populateSelect("engineTypeSelect", opts.enginetype, "ohc");
    populateSelect("cylinderSelect", opts.cylindernumber, "four");
}

function populateSelect(elemId, optionsList, defaultVal) {
    const select = document.getElementById(elemId);
    if (!select) return;
    select.innerHTML = "";
    optionsList.forEach(opt => {
        const el = document.createElement("option");
        el.value = opt;
        el.textContent = opt.toUpperCase();
        if (opt === defaultVal) el.selected = true;
        select.appendChild(el);
    });
}

function updateSlider(valId, val, unit) {
    document.getElementById(valId).innerText = val + unit;
}

function triggerPredict() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(runLivePrediction, 100);
}

async function runLivePrediction() {
    const payload = {
        brand: document.getElementById("brandSelect").value || "toyota",
        carbody: document.getElementById("bodySelect").value || "sedan",
        fueltype: document.getElementById("fuelSelect").value || "gas",
        drivewheel: document.getElementById("driveSelect").value || "fwd",
        enginetype: document.getElementById("engineTypeSelect").value || "ohc",
        cylindernumber: document.getElementById("cylinderSelect").value || "four",
        aspiration: "std",
        doornumber: "four",
        enginelocation: "front",
        wheelbase: 97.0,
        carlength: 172.0,
        carwidth: 65.5,
        carheight: 53.7,
        curbweight: parseFloat(document.getElementById("curbWeightSlider").value),
        enginesize: parseFloat(document.getElementById("engineSizeSlider").value),
        fuelsystem: "mpfi",
        boreratio: 3.3,
        stroke: 3.25,
        compressionratio: 9.0,
        horsepower: parseFloat(document.getElementById("hpSlider").value),
        peakrpm: 5200.0,
        citympg: parseFloat(document.getElementById("cityMpgSlider").value),
        highwaympg: parseFloat(document.getElementById("hwyMpgSlider").value)
    };

    try {
        const res = await fetch("/api/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error("Prediction API call failed");
        currentPredictionData = await res.json();

        updatePredictionUI(currentPredictionData);

    } catch (err) {
        console.error("Prediction error:", err);
    }
}

function updatePredictionUI(data) {
    // Car Image & Overlay
    const carImg = document.getElementById("carPreviewImg");
    const carOverlay = document.getElementById("carImageCategory");
    if (carImg && data.car_image) {
        carImg.src = data.car_image;
        carOverlay.innerText = `${data.inputs.carbody.toUpperCase()} SHOWCASE (${data.inputs.brand.toUpperCase()})`;
    }

    const priceElem = document.getElementById("predictedPrice");
    const currSymbol = document.getElementById("currSymbol");
    const secondaryPrice = document.getElementById("secondaryPrice");
    const confInterval = document.getElementById("confInterval");
    const showroomPrice = document.getElementById("showroomPrice");
    const resalePrice = document.getElementById("resalePrice");
    const tradeInPrice = document.getElementById("tradeInPrice");

    if (currentCurrency === "INR") {
        currSymbol.innerText = "₹";
        priceElem.innerText = data.inr_formatted.replace("₹ ", "");
        secondaryPrice.innerText = `Full Amount: ₹ ${data.predicted_price_inr.toLocaleString()} (Equal to $${data.predicted_price_usd.toLocaleString()} USD)`;
        confInterval.innerText = `${data.lower_bound_inr} — ${data.upper_bound_inr}`;
        showroomPrice.innerText = data.new_car_showroom_inr;
        resalePrice.innerText = data.inr_formatted;
        tradeInPrice.innerText = data.trade_in_offer_inr;
    } else {
        currSymbol.innerText = "$";
        priceElem.innerText = data.predicted_price_usd.toLocaleString("en-US");
        secondaryPrice.innerText = `Equal to ${data.inr_formatted} (₹ ${data.predicted_price_inr.toLocaleString()})`;
        confInterval.innerText = `$${data.lower_bound_usd.toLocaleString()} — $${data.upper_bound_usd.toLocaleString()}`;
        showroomPrice.innerText = `$${(data.predicted_price_usd * 1.25).toLocaleString()}`;
        resalePrice.innerText = `$${data.predicted_price_usd.toLocaleString()}`;
        tradeInPrice.innerText = `$${(data.predicted_price_usd * 0.88).toLocaleString()}`;
    }

    const badge = document.getElementById("tierBadge");
    badge.innerText = data.market_tier;
    badge.style.color = data.tier_color;
    badge.style.borderColor = data.tier_color;

    const driversUl = document.getElementById("driversList");
    driversUl.innerHTML = "";
    data.key_drivers.forEach(driver => {
        const li = document.createElement("li");
        li.innerText = driver;
        driversUl.appendChild(li);
    });

    // Populate Depreciation Schedule Table
    renderDepreciationTable(data.depreciation_schedule);

    // Update Print Certificate details
    document.getElementById("certDate").innerText = new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
    document.getElementById("certBody").innerText = data.inputs.carbody.toUpperCase();
    document.getElementById("certBrand").innerText = data.inputs.brand.toUpperCase();
    document.getElementById("certEngine").innerText = `${data.inputs.enginesize} cc | ${data.inputs.horsepower} HP`;
    document.getElementById("certPrice").innerText = currentCurrency === "INR" ? data.inr_formatted : `$${data.predicted_price_usd.toLocaleString()}`;
    document.getElementById("certRange").innerText = currentCurrency === "INR" ? `${data.lower_bound_inr} — ${data.upper_bound_inr}` : `$${data.lower_bound_usd.toLocaleString()} — $${data.upper_bound_usd.toLocaleString()}`;
    document.getElementById("certShowroom").innerText = showroomPrice.innerText;
    document.getElementById("certTradeIn").innerText = tradeInPrice.innerText;
}

function renderDepreciationTable(schedule) {
    const tbody = document.getElementById("depreciationTableBody");
    if (!tbody || !schedule) return;
    tbody.innerHTML = "";

    schedule.forEach(row => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${row.year}</strong></td>
            <td style="color: #6366f1; font-weight: 700;">${row.price_inr}</td>
            <td>${row.retain_pct} Value Retained</td>
            <td><span class="status-tag">Verified Trend</span></td>
        `;
        tbody.appendChild(tr);
    });
}

// Side by Side Vehicle Comparison
function populateCompareSelects() {
    if (!appMetadata || !appMetadata.categorical_options) return;
    const opts = appMetadata.categorical_options;

    populateSelect("cmpBrandA", opts.brand, "toyota");
    populateSelect("cmpBodyA", opts.carbody, "sedan");
    populateSelect("cmpBrandB", opts.brand, "porsche");
    populateSelect("cmpBodyB", opts.carbody, "convertible");
}

async function runComparison() {
    const carA = {
        brand: document.getElementById("cmpBrandA").value || "toyota",
        carbody: document.getElementById("cmpBodyA").value || "sedan",
        horsepower: parseFloat(document.getElementById("cmpHpA").value) || 120,
        enginesize: parseFloat(document.getElementById("cmpEngineA").value) || 130,
        curbweight: 2400, citympg: 25, highwaympg: 30, fueltype: "gas", drivewheel: "fwd",
        enginetype: "ohc", cylindernumber: "four", aspiration: "std", doornumber: "four",
        enginelocation: "front", wheelbase: 97.0, carlength: 172.0, carwidth: 65.5,
        carheight: 53.7, fuelsystem: "mpfi", boreratio: 3.3, stroke: 3.25,
        compressionratio: 9.0, symboling: 0, peakrpm: 5200.0
    };

    const carB = {
        brand: document.getElementById("cmpBrandB").value || "porsche",
        carbody: document.getElementById("cmpBodyB").value || "convertible",
        horsepower: parseFloat(document.getElementById("cmpHpB").value) || 200,
        enginesize: parseFloat(document.getElementById("cmpEngineB").value) || 180,
        curbweight: 2750, citympg: 18, highwaympg: 25, fueltype: "gas", drivewheel: "rwd",
        enginetype: "ohc", cylindernumber: "six", aspiration: "std", doornumber: "two",
        enginelocation: "front", wheelbase: 97.0, carlength: 172.0, carwidth: 65.5,
        carheight: 53.7, fuelsystem: "mpfi", boreratio: 3.3, stroke: 3.25,
        compressionratio: 9.0, symboling: 0, peakrpm: 5200.0
    };

    try {
        const res = await fetch("/api/compare", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ carA, carB })
        });

        if (!res.ok) throw new Error("Comparison failed");
        const data = await res.json();

        document.getElementById("cmpImgA").src = data.carA.image;
        document.getElementById("cmpPriceA").innerText = currentCurrency === "INR" ? data.carA.price_inr : data.carA.price_usd;

        document.getElementById("cmpImgB").src = data.carB.image;
        document.getElementById("cmpPriceB").innerText = currentCurrency === "INR" ? data.carB.price_inr : data.carB.price_usd;

        document.getElementById("cmpSummaryTitle").innerText = `Valuation Variance: ${data.price_difference}`;
        document.getElementById("cmpSummaryDesc").innerText = `${data.higher_value_car} (${data.higher_value_car === 'Car A' ? data.carA.brand : data.carB.brand}) holds a higher valuation based on engine specs and category metrics.`;

    } catch (err) {
        console.error("Comparison error:", err);
    }
}

// Print Certificate
function printValuationCertificate() {
    window.print();
}

// Presets
function applyPreset(preset) {
    const presets = {
        sports: { brand: "porsche", body: "convertible", fuel: "gas", hp: 207, engine: 194, weight: 2756, cityMpg: 17, hwyMpg: 25 },
        suv: { brand: "buick", body: "wagon", fuel: "gas", hp: 155, engine: 183, weight: 3410, cityMpg: 19, hwyMpg: 24 },
        economy: { brand: "honda", body: "hatchback", fuel: "gas", hp: 76, engine: 92, weight: 2000, cityMpg: 30, hwyMpg: 34 },
        executive: { brand: "bmw", body: "sedan", fuel: "gas", hp: 182, engine: 164, weight: 3230, cityMpg: 16, hwyMpg: 22 }
    };

    const p = presets[preset];
    if (!p) return;

    document.getElementById("brandSelect").value = p.brand;
    document.getElementById("bodySelect").value = p.body;
    document.getElementById("fuelSelect").value = p.fuel;

    setRangeValue("hpSlider", "hpVal", p.hp, " HP");
    setRangeValue("engineSizeSlider", "engineSizeVal", p.engine, " cc");
    setRangeValue("curbWeightSlider", "curbWeightVal", p.weight, " lbs");
    setRangeValue("cityMpgSlider", "cityMpgVal", p.cityMpg, " MPG");
    setRangeValue("hwyMpgSlider", "hwyMpgVal", p.hwyMpg, " MPG");

    triggerPredict();
}

function setRangeValue(sliderId, textId, val, unit) {
    const slider = document.getElementById(sliderId);
    if (slider) {
        slider.value = val;
        updateSlider(textId, val, unit);
    }
}

function resetForm() {
    applyPreset("economy");
}

// Market Trends Charts
async function renderMarketCharts() {
    try {
        const res = await fetch("/api/market-trends");
        if (!res.ok) return;
        const insights = await res.json();

        const avgPrices = currentCurrency === "INR"
            ? insights.brand_averages.avg_prices_inr_lakhs
            : insights.brand_averages.avg_prices_usd;

        createChart("chartBrandAvg", "bar", {
            labels: insights.brand_averages.brands,
            datasets: [{
                label: currentCurrency === "INR" ? "Average Price (₹ Lakhs)" : "Average Price ($ USD)",
                data: avgPrices,
                backgroundColor: "rgba(6, 182, 212, 0.75)",
                borderRadius: 6
            }]
        });

        const hpScatter = currentCurrency === "INR"
            ? insights.scatter_data.map(d => ({ x: d.horsepower, y: d.price_lakhs }))
            : insights.scatter_data.map(d => ({ x: d.horsepower, y: d.price_usd }));

        createChart("chartHpScatter", "scatter", {
            datasets: [{
                label: "Vehicles",
                data: hpScatter,
                backgroundColor: "rgba(236, 72, 153, 0.7)"
            }]
        }, {
            scales: {
                x: { title: { display: true, text: "Engine Power (HP)", color: "#94a3b8" } },
                y: { title: { display: true, text: currentCurrency === "INR" ? "Resale Value (₹ Lakhs)" : "Resale Value ($ USD)", color: "#94a3b8" } }
            }
        });

        const bodyKeys = Object.keys(insights.body_distribution);
        const bodyVals = Object.values(insights.body_distribution);

        createChart("chartBodyPie", "doughnut", {
            labels: bodyKeys,
            datasets: [{
                data: bodyVals,
                backgroundColor: ["#6366f1", "#10b981", "#06b6d4", "#f59e0b", "#ec4899"]
            }]
        });

    } catch (err) {
        console.error("Market trends error:", err);
    }
}

function createChart(canvasId, type, data, extraOptions = {}) {
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    const ctx = document.getElementById(canvasId).getContext("2d");
    chartInstances[canvasId] = new Chart(ctx, {
        type: type,
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: "#f8fafc", font: { family: "Plus Jakarta Sans" } } }
            },
            scales: type !== "doughnut" ? {
                x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255, 255, 255, 0.05)" } },
                y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255, 255, 255, 0.05)" } }
            } : {},
            ...extraOptions
        }
    });
}
