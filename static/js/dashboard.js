
document.addEventListener("DOMContentLoaded", () => {

    // ------------------------------------------
    // FILE UPLOAD INTERACTIONS
    // ------------------------------------------

    const fileInput = document.getElementById("dataset");
    const selectedFileBox = document.getElementById("selected-file");
    const selectedFileName = document.getElementById("selected-file-name");
    const dropzone = document.querySelector(".upload-dropzone");

    if (fileInput) {
        fileInput.addEventListener("change", () => {
            if (fileInput.files.length > 0) {
                const file = fileInput.files[0];

                selectedFileName.textContent = file.name;
                selectedFileBox.classList.remove("hidden");
            }
        });
    }

    // Drag-and-drop visual feedback
    if (dropzone) {
        ["dragenter", "dragover"].forEach(eventName => {
            dropzone.addEventListener(eventName, event => {
                event.preventDefault();
                dropzone.classList.add("dragover");
            });
        });

        ["dragleave", "drop"].forEach(eventName => {
            dropzone.addEventListener(eventName, event => {
                event.preventDefault();
                dropzone.classList.remove("dragover");
            });
        });

        dropzone.addEventListener("drop", event => {
            const files = event.dataTransfer.files;

            if (files.length > 0 && fileInput) {
                fileInput.files = files;

                selectedFileName.textContent = files[0].name;
                selectedFileBox.classList.remove("hidden");
            }
        });
    }


    // ------------------------------------------
    // ANALYSIS FORM LOADING STATE
    // ------------------------------------------

    const analysisForm = document.getElementById("analysis-form");

    if (analysisForm) {
        analysisForm.addEventListener("submit", () => {
            const button = analysisForm.querySelector(
                'button[type="submit"]'
            );

            if (button) {
                button.classList.add("loading");
                button.innerHTML = "⏳ Analyzing...";
            }
        });
    }


    // ------------------------------------------
    // UPLOAD FORM LOADING STATE
    // ------------------------------------------

    const uploadForm = document.getElementById("upload-form");

    if (uploadForm) {
        uploadForm.addEventListener("submit", () => {
            const button = uploadForm.querySelector(
                'button[type="submit"]'
            );

            if (button) {
                button.classList.add("loading");
                button.innerHTML = "⏳ Uploading...";
            }
        });
    }


    // ------------------------------------------
    // ASSOCIATION NETWORK VISUALIZATION
    // ------------------------------------------

    const networkContainer = document.getElementById("network-chart");

    if (networkContainer && typeof Plotly !== "undefined") {
        try {
            const networkData = JSON.parse(
                networkContainer.dataset.network
            );

            const nodes = networkData.nodes || [];
            const edges = networkData.edges || [];

            if (nodes.length === 0) {
                networkContainer.innerHTML =
                    "<p>No network nodes available.</p>";
            } else {

                // Circular layout
                const positions = {};

                nodes.forEach((node, index) => {
                    const angle =
                        (2 * Math.PI * index / nodes.length) -
                        Math.PI / 2;

                    positions[node.id] = {
                        x: Math.cos(angle),
                        y: Math.sin(angle)
                    };
                });

                // Edge coordinates
                const edgeX = [];
                const edgeY = [];

                edges.forEach(edge => {
                    const source = positions[edge.source];
                    const target = positions[edge.target];

                    if (!source || !target) return;

                    edgeX.push(source.x, target.x, null);
                    edgeY.push(source.y, target.y, null);
                });

                const edgeTrace = {
                    x: edgeX,
                    y: edgeY,
                    mode: "lines",
                    type: "scatter",
                    line: {
                        width: 1,
                        color: "#d9d5ed"
                    },
                    hoverinfo: "skip",
                    showlegend: false
                };

                // Node data
                const nodeX = nodes.map(
                    node => positions[node.id].x
                );

                const nodeY = nodes.map(
                    node => positions[node.id].y
                );

                const nodeLabels = nodes.map(
                    node => node.label
            );

                const nodeTrace = {
                    x: nodeX,
                    y: nodeY,
                    mode: "markers+text",
                    type: "scatter",
                    text: nodeLabels,
                    textposition: "top center",
                    textfont: {
                        size: 10,
                        color: "#55546c"
                    },
                    marker: {
                        size: 16,
                        color: "#7968f5",
                        line: {
                            width: 2,
                            color: "#ffffff"
                        }
                    },
                    hovertemplate:
                        "<b>%{text}</b><extra></extra>",
                    showlegend: false
                };

                const layout = {
                    autosize: true,
                    paper_bgcolor: "#ffffff",
                    plot_bgcolor: "#ffffff",
                    margin: {
                        l: 25,
                        r: 25,
                        t: 35,
                        b: 25
                    },
                    xaxis: {
                        visible: false,
                        range: [-1.35, 1.35]
                    },
                    yaxis: {
                        visible: false,
                        range: [-1.35, 1.35],
                        scaleanchor: "x",
                        scaleratio: 1
                    },
                    showlegend: false,
                    hovermode: "closest"
                };

                const config = {
                    responsive: true,
                    displayModeBar: true,
                    displaylogo: false,
                    modeBarButtonsToRemove: [
                        "lasso2d",
                        "select2d"
                    ]
                };

                Plotly.newPlot(
                    networkContainer,
                    [edgeTrace, nodeTrace],
                    layout,
                    config
                );
            }

        } catch (error) {
            console.error("Network visualization error:", error);
            networkContainer.innerHTML =
                "<div class='empty-state'>" +
                "<h3>Could not render network</h3>" +
                "<p>Check the browser console for details.</p>" +
                "</div>";
        }
    }


    // ------------------------------------------
    // SIDEBAR NAVIGATION ACTIVE STATE
    // ------------------------------------------

    const navLinks = document.querySelectorAll(".nav-item");

    navLinks.forEach(link => {
        link.addEventListener("click", () => {
            navLinks.forEach(item => {
                item.classList.remove("active");
            });

            link.classList.add("active");
        });
    });


    // ------------------------------------------
    // SCROLL TO TOP AFTER ANALYSIS
    // ------------------------------------------

    if (document.querySelector(".results-section")) {
        // Results are available; keep the dashboard at the top
        // so the user can navigate the result sections.
    }

});
