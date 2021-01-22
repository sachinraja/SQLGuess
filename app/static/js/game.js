function makeGuess(){
    let guessText = guessInputElement.value.trim();
    if (!guessText) return;

    guessButtonElement.disabled = true;
    socket.emit("guess", guessText);
}

function makeQuery(){
    let queryText = codeMirror.getValue().trim();
    if (!queryText) return;

    queryButtonElement.disabled = true;
    socket.emit("query", queryText);
}

function parseGuessResponse(response){
    guessOutputElement.innerHTML = "";
    if (response["error"]){
        addError(guessOutputElement, response["error"]);
    }

    else{
        if (response["result"]){
            guessButtonElement.disabled = true;
            queryButtonElement.disabled = true;
            addSuccess(guessOutputElement, "Guess is correct!");
            return;
        }
        
        addError(guessOutputElement, "Guess is wrong.");
    }

    guessButtonElement.disabled = false;
}

function parseQueryResponse(response){
    queryOutputElement.innerHTML = "";
    if (response["error"]){
        addError(queryOutputElement, response["error"])
    }
    
    else{
        resultElement.innerHTML = "";
        //generate table
        let thead = document.createElement("thead");
        let theadTr = document.createElement("tr");
        
        let numberTh = document.createElement("th");
        numberTh.scope = "col";
        numberTh.textContent = "#";
        theadTr.appendChild(numberTh);

        for (let column of response["columns"]){
            let newTh = document.createElement("th");
            newTh.scope = "col";
            newTh.textContent = column;
            theadTr.appendChild(newTh);
        }

        thead.appendChild(theadTr);
        resultElement.appendChild(thead);

        let tbody = document.createElement("tbody");

        for ([index, row] of Object.entries(response["result"])){
            let newTr = document.createElement("tr");
            let newTh = document.createElement("th");
            newTh.scope = "row";
            newTh.textContent = index;
            newTr.appendChild(newTh);

            for (let attrValue of row){
                let newTd = document.createElement("td");
                newTd.textContent = attrValue;
                newTr.appendChild(newTd);
            }

            tbody.appendChild(newTr);
        }

        resultElement.appendChild(tbody);
    }

    queryCount++;
    updateQueryCount();

    queryButtonElement.disabled = false;
}

function addError(element, message){
    let newError = document.createElement("div");
    newError.className = "alert alert-danger";
    newError.setAttribute("role", "alert");
    newError.textContent = message;
    element.appendChild(newError);
}

function addSuccess(element, message){
    let newError = document.createElement("div");
    newError.className = "alert alert-success";
    newError.setAttribute("role", "alert");
    newError.textContent = message;
    element.appendChild(newError);
}

function emitStartGame(){
    socket.emit("start_game");
}

function loadRoom(roomStatusArg, currentTime){
    roomStatus = roomStatusArg;
    if (roomStatus == 1){
        timer.setTime(currentTime);
        timer.start();

        hideAllContainers();
        gameRoomContainer.className = "";

        //recalculate dimensions
        codeMirror.refresh();
    }

    else if (roomStatus == 2){
        hideAllContainers();

    }
}

function startGame(){
    timer.start();

    hideAllContainers();
    gameRoomContainer.className = "";

    codeMirror.refresh();
}

class Timer{
    constructor(timerElement){
        this.timerElement = timerElement;
        this.timer = false;
        this.startTime = 80;
        this.currentTime = this.startTime;
    }

    start(){
        this.timer = setInterval(this.update.bind(this), 1000);
    }

    stop(){
        clearInterval(this.timer);
        this.timer = false;
    }

    setTime(seconds){
        this.currentTime = seconds;
    }

    update(){
        this.currentTime--;
        this.timerElement.textContent = this.currentTime;
    }

    reset(){
        this.setTime(this.startTime);
    }
}

function addHint(hintName, hintValue){
    let hintElement = document.createElement("li");
    let hintElementP = document.createElement("p");
    hintElementP.textContent = `${hintName} is `;
    hintElement.appendChild(hintElementP);

    let hintElementStrong = document.createElement("strong");
    hintElementStrong.textContent = hintValue;
    hintElementP.appendChild(hintElementStrong);
    
    hintsContainer.appendChild(hintElement);
}

function parseHintResponse(response){
    let hintName = response["name"];
    let hintValue = response["value"];

    addHint(hintName, hintValue);
}

function updateQueryCount(){
    queryCountElement.textContent = queryCount;
}

function parseEndRoundData(data){
    endRoundDataTBody.innerHTML = "";

    for (let [displayName, points, guessedCorrectly] of data["user_query_counts"]){
        let newTr = document.createElement("tr");

        let tdDisplayName = document.createElement("td");
        tdDisplayName.textContent = displayName;
        newTr.appendChild(tdDisplayName);

        let tdPoints = document.createElement("td");
        tdPoints.textContent = points;
        newTr.appendChild(tdPoints);

        let tdGuessedCorrectly = document.createElement("td");
        tdGuessedCorrectly.className = guessedCorrectly ? "text-success" : "text-danger";
        tdGuessedCorrectly.textContent = guessedCorrectly;
        newTr.appendChild(tdGuessedCorrectly);

        endRoundDataTBody.appendChild(newTr);
    }

    endRoundCorrectLocation.textContent = `Correct Location: ${data["correct_location"]}`;
}

function hideAllContainers(){
    lobbyContainer.className = "d-none";
    gameRoomContainer.className = "d-none";
    endRoundContainer.className = "d-none";
}

function emitNextRound(){
    socket.emit("next_round");
}

function emitEndGame(){
    socket.emit("end_game");
}

function displayEndGame(){
    hideAllContainers();
}

function resetGuessElements(){
    guessInputElement.value = "";
    guessOutputElement.innerHTML = "";
    guessButtonElement.disabled = false;
}

function resetQueryElements(){
    queryOutputElement.innerHTML = "";
    resultElement.innerHTML = "";
    queryButtonElement.disabled = false;
}

function resetCodeMirror(){
    codeMirror.refresh();
    codeMirror.setValue("SELECT foo_id FROM foo WHERE foo_name='bar';")
}

const lobbyContainer = document.getElementById("lobby");
const gameRoomContainer = document.getElementById("gameRoom");
const endRoundContainer = document.getElementById("endRound");
const endGameContainer = document.getElementById("endGame");

const endRoundDataTBody = document.getElementById("endRoundData");
const endRoundCorrectLocation = document.getElementById("correctLocation");

const guessInputElement = document.getElementById("guess");
const guessOutputElement = document.getElementById("guessOutput");
const guessButtonElement = document.getElementById("guessButton");

const queryOutputElement = document.getElementById("queryOutput");
const queryButtonElement = document.getElementById("queryButton");
const queryCountElement = document.getElementById("queryCount");
let queryCount = 0;

const resultElement = document.getElementById("results");
const timer = new Timer(document.getElementById("timer"));

const hintsContainer = document.getElementById("hints");

let roomStatus = 0;

const codeMirror = CodeMirror.fromTextArea(document.getElementById("codeEditor"), 
{
    lineNumbers: true,
    mode: "sql",
    theme: "base16-dark"
});
codeMirror.setValue("SELECT foo_id FROM foo WHERE foo_name='bar';")
codeMirror.setSize(null, 150);

const socket = io();

socket.on("start_game", () => {
    startGame();
});

socket.on("connect", () => {
    socket.emit("add_user");
});

socket.on("guess", response => {
    parseGuessResponse(response);
});

socket.on("query", response => {
    parseQueryResponse(response);
});

socket.on("hint", response => {
    parseHintResponse(response);
});

socket.on("end_round", data => {
    timer.stop();
    parseEndRoundData(JSON.parse(data));

    //clear old data
    hintsContainer.innerHTML = "";
    resetGuessElements();
    resetQueryElements();

    hideAllContainers();
    endRoundContainer.className = "";
});

socket.on("begin_round", () => {
    timer.reset();
    timer.start();

    queryCount = 0;
    updateQueryCount();

    hideAllContainers();
    gameRoomContainer.className = "";
    resetCodeMirror();
});

socket.on("end_game", () => {
    hideAllContainers();
    endGameContainer.className = "";

    timer.stop();
    socket.disconnect();
});

//user events
socket.on("add_user", display_name => {
    addUser(display_name);
});

socket.on("user_reconnect", index => {
    reconnectUser(index);
});

socket.on("user_disconnect", index => {
    disconnectUser(index);
    console.log("disconnect", index);
});

socket.on("join_room", data => {
    let parsedData = JSON.parse(data);
    
    for (user of parsedData["users"])
    {
        addUser(user["display_name"], user["status"]);
    }

    for (hint of parsedData["hints"])
    {
        addHint(hint[0], hint[1]);
    }
    
    queryCount = parsedData["query_count"];
    updateQueryCount();

    if (roomStatus == 2){
        parseEndRoundData(parsedData);

        hideAllContainers();
        endRoundContainer.className = "";
    }
});