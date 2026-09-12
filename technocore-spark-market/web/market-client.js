const SPARK_MARKET_ROOM = "p-jubbic-spark-market";
const TECHNCORE_BASE = "https://technocore.chat";

let marketIdentity = null;

function marketElement(tag, text = "") {
    const element = document.createElement(tag);
    element.textContent = text;
    return element;
}

function marketShortDid(did) {
    if (!did) return "-";
    if (did.length <= 32) return did;
    return did.slice(0, 18) + "..." + did.slice(-8);
}

function setParticipantStatus(text) {
    const element = document.getElementById(
        "participantStatus"
    );

    if (element) {
        element.textContent = text;
    }
}

function renderParticipantIdentity() {
    const didElement =
        document.getElementById("participantDid");

    const connectButton =
        document.getElementById("connectIdentity");

    const createButton =
        document.getElementById("createIdentity");

    const disconnectButton =
        document.getElementById("disconnectIdentity");

    if (!marketIdentity) {
        if (didElement) {
            didElement.textContent = "Not connected";
        }

        if (connectButton) {
            connectButton.style.display = "inline-flex";
        }

        if (createButton) {
            createButton.style.display = "inline-flex";
        }

        if (disconnectButton) {
            disconnectButton.style.display = "none";
        }

        return;
    }

    if (didElement) {
        didElement.textContent =
            marketShortDid(marketIdentity.did);
    }

    if (connectButton) {
        connectButton.style.display = "none";
    }

    if (createButton) {
        createButton.style.display = "none";
    }

    if (disconnectButton) {
        disconnectButton.style.display = "inline-flex";
    }
}

async function connectIdentity() {
    try {
        const identity =
            await SparkIdentity.getIdentity();

        if (!identity) {
            setParticipantStatus(
                "No browser identity exists yet. Create one first."
            );
            return;
        }

        marketIdentity = identity;

        renderParticipantIdentity();

        setParticipantStatus(
            "Connected. Your private signing key stays in this browser."
        );

        if (typeof loadMarket === "function") {
            await loadMarket();
        }

    } catch (error) {
        setParticipantStatus(
            "Connection failed: " + error.message
        );
    }
}

async function createBrowserIdentity() {
    try {
        const identity =
            await SparkIdentity.createIdentity();

        marketIdentity = identity;

        renderParticipantIdentity();

        setParticipantStatus(
            "Identity created and connected. DID: " +
            identity.did
        );

        if (typeof loadMarket === "function") {
            await loadMarket();
        }

    } catch (error) {
        setParticipantStatus(
            "Could not create identity: " +
            error.message
        );
    }
}

function disconnectIdentity() {
    /*
     * Disconnect does NOT delete the key.
     * The browser identity remains stored locally.
     */
    marketIdentity = null;

    renderParticipantIdentity();

    setParticipantStatus(
        "Disconnected. Your browser identity is still stored locally."
    );
}

async function sendMarketEvent(text) {
    if (!marketIdentity) {
        throw new Error(
            "Connect a browser identity first."
        );
    }

    const record =
        await SparkIdentity.signMessage(
            marketIdentity.privateKey,
            marketIdentity.publicKey,
            SPARK_MARKET_ROOM,
            text
        );

    const locallyVerified =
        await SparkIdentity.verifyLocalSignature(
            record
        );

    if (!locallyVerified) {
        throw new Error(
            "Local cryptographic verification failed."
        );
    }

    const url =
        TECHNCORE_BASE +
        "/r/" +
        encodeURIComponent(record.room) +
        "/say-signed/" +
        encodeURIComponent(record.did) +
        "/" +
        encodeURIComponent(record.sig) +
        "/" +
        encodeURIComponent(record.nonce) +
        "/" +
        encodeURIComponent(record.text);

    await fetch(url, {
        method: "GET",
        mode: "no-cors",
        cache: "no-store"
    });

    return record;
}

async function claimMarketTask(taskId, button) {
    try {
        if (!marketIdentity) {
            throw new Error(
                "Connect your browser identity first."
            );
        }

        button.disabled = true;
        button.textContent = "Signing...";

        const text =
            "TASK_CLAIM|" +
            taskId +
            "|" +
            marketIdentity.did;

        await sendMarketEvent(text);

        button.textContent =
            "Claim sent — refreshing...";

        /*
         * Technocore GET writes are fire-and-read.
         * Refresh the market to determine the actual
         * resulting state and handle claim races.
         */
        await new Promise(
            resolve => setTimeout(resolve, 1200)
        );

        await loadMarket();

    } catch (error) {
        button.disabled = false;
        button.textContent = "Claim task";

        setParticipantStatus(
            "Claim failed: " + error.message
        );
    }
}

async function completeMarketTask(
    taskId,
    proof,
    button
) {
    try {
        if (!marketIdentity) {
            throw new Error(
                "Connect your browser identity first."
            );
        }

        proof = proof.trim();

        if (!proof) {
            throw new Error(
                "Completion proof cannot be empty."
            );
        }

        if (proof.includes("|")) {
            throw new Error(
                "Completion proof cannot contain the | character."
            );
        }

        if (proof.length > 1000) {
            throw new Error(
                "Completion proof is too long."
            );
        }

        button.disabled = true;
        button.textContent = "Signing...";

        const text =
            "TASK_COMPLETE|" +
            taskId +
            "|" +
            marketIdentity.did +
            "|" +
            proof;

        await sendMarketEvent(text);

        button.textContent =
            "Completion sent — refreshing...";

        await new Promise(
            resolve => setTimeout(resolve, 1200)
        );

        await loadMarket();

    } catch (error) {
        button.disabled = false;
        button.textContent = "Complete task";

        setParticipantStatus(
            "Completion failed: " +
            error.message
        );
    }
}

function addParticipantActions(card, task) {
    const actions =
        document.createElement("div");

    actions.className = "market-actions";

    if (!marketIdentity) {
        const note =
            marketElement(
                "div",
                "Connect a browser identity to participate."
            );

        note.className = "terminal-note";

        actions.appendChild(note);

        card.appendChild(actions);
        return;
    }

    if (task.status === "OPEN") {
        const button =
            marketElement(
                "button",
                "Claim task"
            );

        button.className =
            "button market-action-button";

        button.type = "button";

        button.addEventListener(
            "click",
            () => claimMarketTask(
                task.task_id,
                button
            )
        );

        actions.appendChild(button);
    }

    if (
        task.status === "CLAIMED" &&
        task.claimed_by === marketIdentity.did
    ) {
        const proofInput =
            document.createElement("input");

        proofInput.type = "text";
        proofInput.maxLength = 1000;
        proofInput.placeholder =
            "Completion proof (URL or short evidence)";
        proofInput.className =
            "market-proof-input";

        const button =
            marketElement(
                "button",
                "Complete task"
            );

        button.className =
            "button market-action-button";

        button.type = "button";

        button.addEventListener(
            "click",
            () => completeMarketTask(
                task.task_id,
                proofInput.value,
                button
            )
        );

        actions.appendChild(proofInput);
        actions.appendChild(button);
    }

    if (
        task.status === "CLAIMED" &&
        task.claimed_by !== marketIdentity.did
    ) {
        const note =
            marketElement(
                "div",
                "This task is currently claimed by another participant."
            );

        note.className = "terminal-note";

        actions.appendChild(note);
    }

    card.appendChild(actions);
}

function initialiseParticipantUI() {
    const connect =
        document.getElementById(
            "connectIdentity"
        );

    const create =
        document.getElementById(
            "createIdentity"
        );

    const disconnect =
        document.getElementById(
            "disconnectIdentity"
        );

    if (connect) {
        connect.addEventListener(
            "click",
            connectIdentity
        );
    }

    if (create) {
        create.addEventListener(
            "click",
            createBrowserIdentity
        );
    }

    if (disconnect) {
        disconnect.addEventListener(
            "click",
            disconnectIdentity
        );
    }

    renderParticipantIdentity();

    connectIdentity();
}

window.addParticipantActions =
    addParticipantActions;

window.addEventListener(
    "DOMContentLoaded",
    initialiseParticipantUI
);
