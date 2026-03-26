// ── ASX200 ticker list for autocomplete ──────────────────
const ASX200_TICKERS = [
    "BHP","CBA","CSL","NAB","WBC","ANZ","WES","MQG","RIO","TLS",
    "GMG","WDS","FMG","TCL","STO","REA","COL","ALL","IAG","QBE",
    "BXB","APA","NST","NEM","NCM","EVN","OZL","S32","AWC","BSL",
    "WOW","SVW","TWE","CWY","ASX","CPU","DXS","GPT","SGP","SCG",
    "MGR","VCX","URW","LLC","ABP","CLW","CMW","HDN","HPI","BWP",
    "ALQ","ANN","ARB","ALD","AMP","AMC","APT","APX","APE","AFI",
    "ARG","AIA","AGI","AUB","AZJ","BAP","BEN","BOQ","BKW","BLD",
    "BRG","CAR","CHC","CIM","CIP","CGF","CCP","CCX","CKF","CIA",
    "COH","CVW","CTD","DHG","DOW","DMP","EBO","ELD","EMR","EML",
    "ERA","EVT","FBU","FLT","GNC","GOR","GWA","HLS","HVN","IEL",
    "IGO","ILU","ING","IPL","JBH","JHX","JHG","KGN","LNK","LYC",
    "MCY","MIN","MLT","MMS","MPL","MTS","MVF","MYX","NHF","NUF",
    "NWS","ORA","ORG","ORI","OSH","PBH","PDL","PLS","PME","PPT",
    "PRN","PSQ","PTM","QAN","QUB","RBL","RHC","RMD","RRL","RSG",
    "SAR","SBM","SEK","SFR","SGM","SHL","SIG","SKC","SKI","SLK",
    "SOL","SOM","SPK","SPL","SRX","SSM","STO","SUL","SUN","TAH",
    "TGR","THL","TNE","TPG","TRS","TSI","UNI","URF","VEA","VHT",
    "WBC","WEB","WGX","WHC","WOR","WSA","XRO","YAL","Z1P","ZIM"
];

// ── Populate datalist for native autocomplete ─────────────
document.addEventListener("DOMContentLoaded", function () {
    const datalist = document.getElementById("tickerList");
    if (datalist) {
        ASX200_TICKERS.forEach(function (ticker) {
            const option = document.createElement("option");
            option.value = ticker;
            datalist.appendChild(option);
        });
    }

    // Auto-uppercase ticker input as user types
    const tickerInput = document.getElementById("tickerInput");
    if (tickerInput) {
        tickerInput.addEventListener("input", function () {
            const pos = this.selectionStart;
            this.value = this.value.toUpperCase();
            this.setSelectionRange(pos, pos);
        });
    }

    // ── Form submission — show loading overlay ────────────
    const form = document.getElementById("analyseForm");
    if (form) {
        form.addEventListener("submit", function (e) {
            const ticker = tickerInput ? tickerInput.value.trim() : "";
            if (!ticker) return; // Let HTML5 validation handle empty input

            // Show loading overlay
            const overlay = document.getElementById("loadingOverlay");
            if (overlay) {
                overlay.style.display = "flex";
            }

            // Disable button to prevent double-submit
            const btn = document.getElementById("analyseBtn");
            if (btn) {
                btn.querySelector(".btn-text").style.display = "none";
                btn.querySelector(".btn-loading").style.display = "flex";
                btn.disabled = true;
            }

            // Start staged progress messages
            startLoadingSequence();
        });
    }
});

// ── Staged loading messages ───────────────────────────────
// Mimics the real pipeline stages so the wait feels purposeful
function startLoadingSequence() {
    const stages = [
        { message: "Fetching live ASX data...",          progress: 8,  delay: 0 },
        { message: "Pulling recent news...",             progress: 15, delay: 3000 },
        { message: "Agent 1: Reading the financials...", progress: 30, delay: 6000 },
        { message: "Agent 1: Assigning signals...",      progress: 45, delay: 14000 },
        { message: "Agent 1: Triaging concerns...",      progress: 55, delay: 20000 },
        { message: "Agent 2: Running web search...",     progress: 65, delay: 26000 },
        { message: "Agent 2: Stress-testing findings...",progress: 78, delay: 32000 },
        { message: "Agent 2: Compliance check...",       progress: 88, delay: 38000 },
        { message: "Finalising your report...",          progress: 96, delay: 44000 },
    ];

    const stageEl = document.getElementById("loadingStage");
    const barEl   = document.getElementById("loadingBar");

    stages.forEach(function (stage) {
        setTimeout(function () {
            if (stageEl) {
                stageEl.style.opacity = "0";
                setTimeout(function () {
                    stageEl.textContent = stage.message;
                    stageEl.style.opacity = "1";
                }, 150);
            }
            if (barEl) {
                barEl.style.width = stage.progress + "%";
            }
        }, stage.delay);
    });
}
