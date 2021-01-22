function addUser(display_name, status){
    const colDiv = document.createElement("div");
    colDiv.className = "col-sm-3 mt-2 display-name";
    displayNameRow.appendChild(colDiv);

    const cardDiv = document.createElement("div");
    cardDiv.className = "card bg-warning text-light";
    colDiv.appendChild(cardDiv);

    const cardBodyDiv = document.createElement("div");
    cardBodyDiv.className = "card-body";
    cardDiv.appendChild(cardBodyDiv);

    const cardTitle = document.createElement("h5");
    cardTitle.className = "card-title text-center";
    cardTitle.textContent = display_name;
    cardBodyDiv.appendChild(cardTitle);

    if (status === 0){
        const mutedDisconnectText = document.createElement("h5");
        mutedDisconnectText.className = "text-muted";
        mutedDisconnectText.textContent = "Disconnected";
        cardBodyDiv.appendChild(mutedDisconnectText);
    }
}

function removeUser(index){
    userDivs.splice(index, 1);
}

function reconnectUser(index){
    //col div
    const cardBodyDiv = userDivs[index]
    //card div
    .getElementsByTagName("div")[0]
    //card body div
    .getElementsByTagName("div")[0];
    
    cardBodyDiv.getElementsByClassName("text-muted")[0]?.remove();
}

function disconnectUser(index){
    //col div
    const cardBodyDiv = userDivs[index]
    //card div
    .getElementsByTagName("div")[0]
    //card body div
    .getElementsByTagName("div")[0];

    const mutedDisconnectText = document.createElement("h5");
    mutedDisconnectText.className = "text-muted";
    mutedDisconnectText.textContent = "Disconnected";
    cardBodyDiv.appendChild(mutedDisconnectText);
}

const displayNameRow = document.getElementById("displayNames");
const userDivs = displayNameRow.getElementsByClassName("display-name");