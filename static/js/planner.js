document.addEventListener("DOMContentLoaded", function () {

    const body = document.getElementById("participants-body");
    const addParticipantBtn = document.getElementById("add-participant");
    const addMeetingBtn = document.getElementById("add-meeting");
    const clearBtn = document.getElementById("clear-all");
    const generateBtn = document.getElementById("generate-itinerary");
    const currentDate = document.getElementById("current-date");

    let participantCount = 0;
    let meetingCount = 3;


    // =========================
    // CURRENT DATE
    // =========================

    if (currentDate) {

        currentDate.textContent =
            new Date().toLocaleDateString("en-GB", {
                day: "2-digit",
                month: "short",
                year: "numeric"
            });

    }


    // =========================
    // CSRF COOKIE
    // =========================

    function getCookie(name) {

        let cookieValue = null;

        if (document.cookie && document.cookie !== "") {

            const cookies = document.cookie.split(";");

            for (let cookie of cookies) {

                cookie = cookie.trim();

                if (cookie.startsWith(name + "=")) {

                    cookieValue = decodeURIComponent(
                        cookie.substring(name.length + 1)
                    );

                    break;
                }

            }

        }

        return cookieValue;
    }


    // =========================
    // ADD PARTICIPANT
    // =========================

    function addParticipant() {

        participantCount++;

        const id = participantCount;

        const row = document.createElement("tr");

        row.className = "participant-row";
        row.dataset.participantId = id;

        row.innerHTML = `

            <td class="participant-number">
                ${id}
            </td>

            <td>
                <input
                    type="text"
                    name="participant_${id}_name"
                    placeholder="Participant name">
            </td>

            <td>
                <input
                    type="text"
                    name="participant_${id}_department"
                    placeholder="Department">
            </td>

            <td>
                <input
                    type="text"
                    name="participant_${id}_location"
                    class="location-input location-search"
                    placeholder="Current location"
                    autocomplete="off">
            </td>

            ${meetingInputs(id, 1)}
            ${meetingInputs(id, 2)}
            ${meetingInputs(id, 3)}

            <td>
                <button
                    type="button"
                    class="remove-participant"
                    title="Remove participant">
                    ×
                </button>
            </td>

        `;

        body.appendChild(row);

    }


    // =========================
    // MEETING INPUTS
    // =========================

    function meetingInputs(participantId, number) {

        return `

            <td>

                <input
                    type="text"
                    class="meeting-location location-search"
                    name="participant_${participantId}_meeting${number}_location"
                    placeholder="${number === 3 ? "Optional" : "Location"}"
                    autocomplete="off">

            </td>


            <td>

                <input
                    type="date"
                    name="participant_${participantId}_meeting${number}_date">

            </td>


            <td>

                <div class="time-picker">

                    <select
                        name="participant_${participantId}_meeting${number}_hour"
                        class="time-hour">

                        <option value="">HH</option>

                        ${Array.from(
                            { length: 12 },
                            (_, i) => {

                                const hour =
                                    String(i + 1).padStart(2, "0");

                                return `
                                    <option value="${hour}">
                                        ${hour}
                                    </option>
                                `;

                            }
                        ).join("")}

                    </select>


                    <select
                        name="participant_${participantId}_meeting${number}_minute"
                        class="time-minute">

                        <option value="">MM</option>

                        <option value="00">00</option>
                        <option value="05">05</option>
                        <option value="10">10</option>
                        <option value="15">15</option>
                        <option value="20">20</option>
                        <option value="25">25</option>
                        <option value="30">30</option>
                        <option value="35">35</option>
                        <option value="40">40</option>
                        <option value="45">45</option>
                        <option value="50">50</option>
                        <option value="55">55</option>

                    </select>


                    <select
                        name="participant_${participantId}_meeting${number}_ampm"
                        class="time-ampm">

                        <option value="">AM/PM</option>
                        <option value="AM">AM</option>
                        <option value="PM">PM</option>

                    </select>

                </div>

            </td>


            <td>

                <select
                    name="participant_${participantId}_meeting${number}_sleepover">

                    <option value="">-</option>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>

                </select>

            </td>

        `;

    }


    // =========================
    // ADD MEETING
    // =========================

    function addMeeting() {

        meetingCount++;

        const number = meetingCount;

        const table =
            document.getElementById("participants-table");

        const headerRows =
            table.querySelectorAll("thead tr");

        const mainHeader = headerRows[0];
        const subHeader = headerRows[1];


        const meetingHeader =
            document.createElement("th");

        meetingHeader.colSpan = 4;

        meetingHeader.className =
            "meeting-header";

        meetingHeader.textContent =
            "📅 Meeting Location " + number;


        const actionsHeader =
            mainHeader.lastElementChild;

        mainHeader.insertBefore(
            meetingHeader,
            actionsHeader
        );


        const subHeaders = [
            "Location",
            "Date",
            "Time",
            "Sleepover?"
        ];


        subHeaders.forEach(function (text) {

            const th =
                document.createElement("th");

            th.textContent = text;

            subHeader.appendChild(th);

        });


        body.querySelectorAll(
            ".participant-row"
        ).forEach(function (row) {

            const participantId =
                row.dataset.participantId;

            const actionCell =
                row.lastElementChild;

            const temp =
                document.createElement("tr");

            temp.innerHTML =
                meetingInputs(
                    participantId,
                    number
                );

            Array.from(
                temp.children
            ).forEach(function (cell) {

                row.insertBefore(
                    cell,
                    actionCell
                );

            });

        });

    }
        // =========================
    // BUTTONS
    // =========================

    if (addParticipantBtn) {

        addParticipantBtn.addEventListener(
            "click",
            addParticipant
        );

    }


    if (addMeetingBtn) {

        addMeetingBtn.addEventListener(
            "click",
            addMeeting
        );

    }


    // =========================
    // REMOVE PARTICIPANT
    // =========================

    body.addEventListener(
        "click",
        function (event) {

            if (
                event.target.classList.contains(
                    "remove-participant"
                )
            ) {

                const row =
                    event.target.closest(
                        ".participant-row"
                    );

                if (row) {
                    row.remove();
                }


                // Renumber participants

                body.querySelectorAll(
                    ".participant-number"
                ).forEach(
                    function (cell, index) {

                        cell.textContent =
                            index + 1;

                    }
                );

            }

        }
    );


    // =========================
    // CLEAR ALL
    // =========================

    if (clearBtn) {

        clearBtn.addEventListener(
            "click",
            function () {

                if (
                    !confirm(
                        "Clear all participants and meeting information?"
                    )
                ) {
                    return;
                }


                body.innerHTML = "";

                participantCount = 0;


                // Start again with 3 participants

                addParticipant();
                addParticipant();
                addParticipant();

            }
        );

    }


    // =========================
    // GENERATE ITINERARY
    // =========================

    if (generateBtn) {

        generateBtn.addEventListener(
            "click",
            function () {

                const rows =
                    document.querySelectorAll(
                        ".participant-row"
                    );

                const participants = [];


                // Read every participant

                rows.forEach(
                    function (row) {

                        const participantId =
                            row.dataset.participantId;


                        const nameInput =
                            row.querySelector(
                                `[name="participant_${participantId}_name"]`
                            );


                        const departmentInput =
                            row.querySelector(
                                `[name="participant_${participantId}_department"]`
                            );


                        const locationInput =
                            row.querySelector(
                                `[name="participant_${participantId}_location"]`
                            );


                        const participant = {

                            name:
                                nameInput
                                    ? nameInput.value.trim()
                                    : "",

                            department:
                                departmentInput
                                    ? departmentInput.value.trim()
                                    : "",

                            current_location:
                                locationInput
                                    ? locationInput.value.trim()
                                    : "",

                            latitude:
                                locationInput
                                    ? (
                                        locationInput.dataset.latitude ||
                                        null
                                    )
                                    : null,

                            longitude:
                                locationInput
                                    ? (
                                        locationInput.dataset.longitude ||
                                        null
                                    )
                                    : null,

                            meetings: []

                        };


                        // =========================
                        // READ ALL MEETINGS
                        // =========================

                        for (
                            let number = 1;
                            number <= meetingCount;
                            number++
                        ) {

                            const locationInput =
                                row.querySelector(
                                    `[name="participant_${participantId}_meeting${number}_location"]`
                                );


                            if (!locationInput) {
                                continue;
                            }


                            const location =
                                locationInput.value.trim();


                            // Empty meeting is allowed
                            // especially Meeting 3+

                            if (!location) {
                                continue;
                            }


                            const dateInput =
                                row.querySelector(
                                    `[name="participant_${participantId}_meeting${number}_date"]`
                                );


                            const hourInput =
                                row.querySelector(
                                    `[name="participant_${participantId}_meeting${number}_hour"]`
                                );


                            const minuteInput =
                                row.querySelector(
                                    `[name="participant_${participantId}_meeting${number}_minute"]`
                                );


                            const ampmInput =
                                row.querySelector(
                                    `[name="participant_${participantId}_meeting${number}_ampm"]`
                                );


                            const sleepoverInput =
                                row.querySelector(
                                    `[name="participant_${participantId}_meeting${number}_sleepover"]`
                                );


                            const meeting = {

                                number:
                                    number,

                                location:
                                    location,

                                latitude:
                                    locationInput.dataset.latitude ||
                                    null,

                                longitude:
                                    locationInput.dataset.longitude ||
                                    null,

                                date:
                                    dateInput
                                        ? dateInput.value
                                        : "",

                                time:
                                    (
                                        hourInput
                                            ? hourInput.value
                                            : ""
                                    ) +
                                    ":" +
                                    (
                                        minuteInput
                                            ? minuteInput.value
                                            : ""
                                    ) +
                                    " " +
                                    (
                                        ampmInput
                                            ? ampmInput.value
                                            : ""
                                    ),

                                sleepover:
                                    sleepoverInput
                                        ? sleepoverInput.value
                                        : ""

                            };


                            participant.meetings.push(
                                meeting
                            );

                        }


                        participants.push(
                            participant
                        );

                    }
                );


                console.log(
                    "Data being sent to Django:",
                    participants
                );


                // =========================
                // SEND TO DJANGO
                // =========================

                fetch(
                    "/generate-itinerary/",
                    {

                        method: "POST",

                        headers: {

                            "Content-Type":
                                "application/json",

                            "X-CSRFToken":
                                getCookie(
                                    "csrftoken"
                                )

                        },

                        body:
                            JSON.stringify(
                                {
                                    participants:
                                        participants
                                }
                            )

                    }
                )

                .then(
                    function (response) {

                        if (!response.ok) {

                            throw new Error(
                                "Server returned " +
                                response.status
                            );

                        }

                        return response.json();

                    }
                )

                .then(
                    function (data) {

                        console.log(
                            "Django response:",
                            data
                        );


                        if (data.success) {

                            alert(
                                data.message
                            );


                            // Render itinerary
                            // only once

                            if (
                                data.itinerary &&
                                typeof renderFullItinerary ===
                                "function"
                            ) {

                                renderFullItinerary(
                                    data.itinerary
                                );

                            }

                        } else {

                            alert(
                                "Error: " +
                                data.message
                            );

                        }

                    }
                )

                .catch(
                    function (error) {

                        console.error(
                            "Connection error:",
                            error
                        );

                        alert(
                            "Could not connect to Django."
                        );

                    }
                );

            }
        );

    }
        // =========================
    // WORLDWIDE LOCATION SEARCH
    // =========================

    document.addEventListener(
        "input",
        function (event) {

            if (
                !event.target.classList.contains(
                    "location-search"
                )
            ) {
                return;
            }


            const input =
                event.target;

            const query =
                input.value.trim();


            // Remove old suggestions

            removeSuggestions();


            // Clear coordinates when user
            // changes the typed location

            delete input.dataset.latitude;
            delete input.dataset.longitude;


            if (query.length < 3) {
                return;
            }


            // Stop previous search timer

            clearTimeout(
                input.searchTimer
            );


            // Wait before searching

            input.searchTimer =
                setTimeout(
                    function () {

                        fetch(
                            "https://nominatim.openstreetmap.org/search?" +
                            new URLSearchParams({

                                q: query,

                                format: "json",

                                addressdetails: "1",

                                limit: "5",

                                // Worldwide search

                                "accept-language":
                                    "en"

                            }),

                            {
                                headers: {
                                    "Accept":
                                        "application/json"
                                }
                            }
                        )

                        .then(
                            function (response) {

                                if (!response.ok) {

                                    throw new Error(
                                        "Location search failed"
                                    );

                                }

                                return response.json();

                            }
                        )

                        .then(
                            function (results) {

                                showSuggestions(
                                    input,
                                    results
                                );

                            }
                        )

                        .catch(
                            function (error) {

                                console.log(
                                    "Location error:",
                                    error
                                );

                            }
                        );

                    },
                    600
                );

        }
    );


    // =========================
    // SHOW LOCATION SUGGESTIONS
    // =========================

    function showSuggestions(
        input,
        results
    ) {

        removeSuggestions();


        if (
            !results ||
            !results.length
        ) {
            return;
        }


        const box =
            document.createElement("div");


        box.id =
            "location-suggestions";


        box.style.cssText = `

            position: fixed;

            background: white;

            border: 1px solid #b9d3ec;

            border-radius: 6px;

            box-shadow:
                0 4px 12px rgba(0,0,0,.15);

            z-index: 99999;

            max-height: 250px;

            overflow-y: auto;

            font-family: Arial, sans-serif;

        `;


        const rect =
            input.getBoundingClientRect();


        box.style.left =
            rect.left + "px";


        box.style.top =
            rect.bottom + "px";


        box.style.width =
            Math.max(
                rect.width,
                300
            ) + "px";


        results.forEach(
            function (place) {

                const option =
                    document.createElement("div");


                option.textContent =
                    place.display_name;


                option.style.cssText = `

                    padding: 10px;

                    cursor: pointer;

                    font-size: 12px;

                    border-bottom:
                        1px solid #eeeeee;

                `;


                option.addEventListener(
                    "mouseenter",
                    function () {

                        option.style.background =
                            "#eef6ff";

                    }
                );


                option.addEventListener(
                    "mouseleave",
                    function () {

                        option.style.background =
                            "white";

                    }
                );


                option.addEventListener(
                    "mousedown",
                    function () {

                        // Save selected location

                        input.value =
                            place.display_name;


                        // Save coordinates

                        input.dataset.latitude =
                            place.lat;


                        input.dataset.longitude =
                            place.lon;


                        removeSuggestions();

                    }
                );


                box.appendChild(
                    option
                );

            }
        );


        document.body.appendChild(
            box
        );

    }


    // =========================
    // REMOVE SUGGESTIONS
    // =========================

    function removeSuggestions() {

        const box =
            document.getElementById(
                "location-suggestions"
            );


        if (box) {
            box.remove();
        }

    }


    // =========================
    // CLOSE SUGGESTIONS
    // =========================

    document.addEventListener(
        "click",
        function (event) {

            if (
                !event.target.classList.contains(
                    "location-search"
                )
            ) {

                removeSuggestions();

            }

        }
    );
        // =========================
    // RENDER GENERATED ITINERARY
    // =========================

    function renderFullItinerary(itinerary) {

        const output =
            document.getElementById(
                "generated-itinerary"
            );

        const tabs =
            document.getElementById(
                "participant-tabs"
            );

        const commonBox =
            document.getElementById(
                "common-meetings"
            );

        const summary =
            document.getElementById(
                "trip-summary"
            );


        if (!output) {
            return;
        }


        output.innerHTML = "";


        if (tabs) {
            tabs.innerHTML = "";
        }


        // =========================
        // NO ITINERARY
        // =========================

        if (
            !itinerary ||
            !itinerary.length
        ) {

            output.innerHTML = `

                <div class="empty-itinerary">

                    <div class="empty-icon">
                        ✈
                    </div>

                    <h3>
                        No itinerary available
                    </h3>

                    <p>
                        Please enter at least one
                        participant with meeting
                        information.
                    </p>

                </div>

            `;

            return;
        }


        // =========================
        // COMMON MEETINGS
        // =========================

        const commonMeetings = {};


        itinerary.forEach(
            function (participant) {

                (
                    participant.meetings || []
                ).forEach(
                    function (meeting) {

                        const key = [

                            String(
                                meeting.location || ""
                            )
                                .trim()
                                .toLowerCase(),

                            meeting.date || "",

                            meeting.time || ""

                        ].join("|");


                        if (
                            !commonMeetings[key]
                        ) {

                            commonMeetings[key] = {

                                location:
                                    meeting.location,

                                date:
                                    meeting.date,

                                time:
                                    meeting.time,

                                participants: []

                            };

                        }


                        commonMeetings[key]
                            .participants
                            .push(
                                participant.name ||
                                "Participant"
                            );

                    }
                );

            }
        );


        const commonList =
            Object.values(
                commonMeetings
            ).filter(
                function (item) {

                    return (
                        item.participants.length > 1
                    );

                }
            );


        if (commonBox) {

            if (!commonList.length) {

                commonBox.innerHTML = `

                    <p class="muted">
                        No common meetings found.
                    </p>

                `;

            } else {

                commonBox.innerHTML =
                    commonList.map(
                        function (item) {

                            return `

                                <div
                                    class="common-meeting-item">

                                    <strong>
                                        ${escapeHtml(
                                            item.location
                                        )}
                                    </strong>

                                    <div>
                                        ${escapeHtml(
                                            item.date || ""
                                        )}
                                        ${escapeHtml(
                                            item.time || ""
                                        )}
                                    </div>

                                    <div>
                                        Participants:
                                        ${item.participants
                                            .map(
                                                escapeHtml
                                            )
                                            .join(", ")}
                                    </div>

                                </div>

                            `;

                        }
                    ).join("");

            }

        }


        // =========================
        // TRIP SUMMARY
        // =========================

        let meetingTotal = 0;

        let flightTotal = 0;

        let hotelNights = 0;


        itinerary.forEach(
            function (participant) {

                meetingTotal +=
                    (
                        participant.meetings || []
                    ).length;


                (
                    participant.days || []
                ).forEach(
                    function (day) {

                        (
                            day.events || []
                        ).forEach(
                            function (event) {

                                const type =
                                    String(
                                        event.type || ""
                                    ).toLowerCase();


                                if (
                                    type === "flight"
                                ) {

                                    flightTotal++;

                                }


                                if (
                                    event.sleepover === true
                                ) {

                                    hotelNights++;

                                }

                            }
                        );

                    }
                );

            }
        );


        if (summary) {

            summary.innerHTML = `

                <li>
                    Total Flights:
                    <strong>
                        ${flightTotal}
                    </strong>
                </li>

                <li>
                    Total Hotel Nights:
                    <strong>
                        ${hotelNights}
                    </strong>
                </li>

                <li>
                    Meetings:
                    <strong>
                        ${meetingTotal}
                    </strong>
                </li>

                <li>
                    Estimated Cost:
                    <strong>
                        Not calculated
                    </strong>
                </li>

            `;

        }


        // =========================
        // PARTICIPANT TABS
        // =========================

        if (tabs) {

            itinerary.forEach(
                function (participant, index) {

                    const tab =
                        document.createElement(
                            "button"
                        );


                    tab.type = "button";


                    tab.className =
                        "participant-tab" +
                        (
                            index === 0
                                ? " active"
                                : ""
                        );


                    tab.textContent =
                        participant.name ||
                        "Participant " +
                        (index + 1);


                    tab.addEventListener(
                        "click",
                        function () {

                            tabs.querySelectorAll(
                                ".participant-tab"
                            ).forEach(
                                function (button) {

                                    button.classList.remove(
                                        "active"
                                    );

                                }
                            );


                            tab.classList.add(
                                "active"
                            );


                            document
                                .querySelectorAll(
                                    ".participant-itinerary-card"
                                )
                                .forEach(
                                    function (
                                        card,
                                        cardIndex
                                    ) {

                                        card.style.display =
                                            cardIndex === index
                                                ? "block"
                                                : "none";

                                    }
                                );

                        }
                    );


                    tabs.appendChild(tab);

                }
            );

        }


        // =========================
        // PARTICIPANT CARDS
        // =========================

        itinerary.forEach(
            function (participant, index) {

                const card =
                    document.createElement(
                        "div"
                    );


                card.className =
                    "participant-itinerary-card";


                card.style.display =
                    index === 0
                        ? "block"
                        : "none";


                const meetings =
                    participant.meetings || [];


                const days =
                    participant.days || [];


                const firstMeeting =
                    meetings.length
                        ? meetings[0]
                        : null;


                const routeText =
                    firstMeeting

                        ? (
                            (
                                participant.current_location ||
                                "Start"
                            ) +
                            " → " +
                            firstMeeting.location
                        )

                        : (
                            participant.current_location ||
                            "Route not available"
                        );


             card.innerHTML = `

    <div class="participant-itinerary-header reference-participant-row">

        <div class="participant-header-main">

            <div class="participant-avatar">
                👤
            </div>

            <div class="participant-header-info">

                <div class="participant-name-row">

                    <h2>
                        ${escapeHtml(
                            participant.name ||
                            "Participant " + (index + 1)
                        )}
                    </h2>

                    <span class="participant-divider">|</span>

                    <span class="participant-route">
                        ${escapeHtml(routeText)}
                    </span>

                </div>

            </div>

        </div>

        <div class="participant-header-right">

            <span class="participant-meeting-count">
                ${meetings.length}
                ${
                    meetings.length === 1
                        ? " Meeting"
                        : " Meetings"
                }
            </span>

            <span class="participant-expand-icon">
                ▼
            </span>

        </div>

    </div>

    <div class="itinerary-days-grid"></div>

`;

                const daysContainer =
                    card.querySelector(
                        ".itinerary-days-grid"
                    );


                // =========================
                // CREATE DAYS IF NEEDED
                // =========================

                if (
                    !days.length &&
                    meetings.length
                ) {

                    const generatedDays = {};


                    meetings.forEach(
                        function (meeting) {

                            if (
                                !generatedDays[
                                    meeting.date
                                ]
                            ) {

                                generatedDays[
                                    meeting.date
                                ] = {

                                    date:
                                        meeting.date,

                                    events: []

                                };

                            }


                            generatedDays[
                                meeting.date
                            ]
                                .events
                                .push({

                                    time:
                                        meeting.time,

                                    title:
                                        "Meeting " +
                                        String(
                                            meeting.number ||
                                            ""
                                        ),

                                    type:
                                        "meeting",

                                    location:
                                        meeting.location,

                                    description:
                                        "Business Meeting",

                                    sleepover:
                                        meeting.sleepover ===
                                        true ||
                                        meeting.sleepover ===
                                        "yes"

                                });

                        }
                    );


                    Object.values(
                        generatedDays
                    ).forEach(
                        function (day) {

                            days.push(day);

                        }
                    );

                }


                // =========================
                // DISPLAY EACH DAY
                // =========================

                days.forEach(
                    function (day) {

                        const dayCard =
                            document.createElement(
                                "div"
                            );


                        dayCard.className =
                            "itinerary-day-card";


                        dayCard.innerHTML = `

                            <div
                                class="day-card-header">

                                <div>

                                    <span
                                        class="day-label">

                                        DAY

                                    </span>

                                    <strong>

                                        ${escapeHtml(
                                            formatDate(
                                                day.date
                                            )
                                        )}

                                    </strong>

                                </div>

                            </div>


                            <div
                                class="day-events">
                            </div>

                        `;


                        const eventsContainer =
                            dayCard.querySelector(
                                ".day-events"
                            );


                        const events =
                            day.events || [];


                        if (!events.length) {

                            eventsContainer.innerHTML = `

                                <div
                                    class="itinerary-event">

                                    <div
                                        class="event-time">

                                        —

                                    </div>

                                    <div
                                        class="event-content">

                                        <strong>
                                            No events
                                        </strong>

                                    </div>

                                </div>

                            `;

                        } else {

                            events.forEach(
                                function (event) {

                                    eventsContainer.appendChild(
                                        createItineraryEvent(
                                            event
                                        )
                                    );


                                    if (
                                        event.sleepover === true ||
                                        event.sleepover === "yes"
                                    ) {

                                        const overnight =
                                            document.createElement(
                                                "div"
                                            );


                                        overnight.className =
                                            "overnight-bar";


                                        overnight.innerHTML = `

                                            🛏️

                                            <strong>
                                                Overnight stay
                                            </strong>

                                            <span>
                                                Hotel / rest
                                                after the meeting
                                            </span>

                                        `;


                                        eventsContainer.appendChild(
                                            overnight
                                        );

                                    }

                                }
                            );

                        }


                        daysContainer.appendChild(
                            dayCard
                        );

                    }
                );


                // =========================
                // RETURN JOURNEY
                // =========================

                if (meetings.length) {

                    const returnBox =
                        document.createElement(
                            "div"
                        );


                    returnBox.className =
                        "itinerary-event return-event";


                    returnBox.innerHTML = `

                        <div class="event-time">
                            ↩
                        </div>

                        <div class="event-content">

                            <strong>
                                Return journey
                            </strong>

                            <div>
                                Return to original
                                location:
                                ${escapeHtml(
                                    participant.current_location ||
                                    "Starting location"
                                )}
                            </div>

                            <div class="event-note">

                                Detailed route, distance
                                and travel time will be
                                calculated in the next
                                travel-planning step.

                            </div>

                        </div>

                    `;


                    const lastDayCard =
    daysContainer.querySelector(
        ".itinerary-day-card:last-of-type"
    );

if (lastDayCard) {

    const lastDayEvents =
        lastDayCard.querySelector(
            ".day-events"
        );

    if (lastDayEvents) {
        lastDayEvents.appendChild(returnBox);
    }

} else {

    daysContainer.appendChild(returnBox);

}

                }


                output.appendChild(
                    card
                );

            }
        );


        // =========================
        // HELPFUL LINKS
        // =========================

        const flightLink =
            document.getElementById(
                "flight-search-link"
            );


        if (flightLink) {

            flightLink.href =
                "https://www.google.com/travel/flights";

            flightLink.target =
                "_blank";

        }


        const hotelLink =
            document.getElementById(
                "hotel-search-link"
            );


        if (hotelLink) {

            hotelLink.href =
                "https://www.google.com/travel/hotels";

            hotelLink.target =
                "_blank";

        }

    }


    // =========================
    // CREATE ITINERARY EVENT
    // =========================

    function createItineraryEvent(event) {

    const item = document.createElement("div");

    item.className = "itinerary-event";

    const type = String(event.type || "").toLowerCase();

    let icon = "📍";

    if (type === "meeting") icon = "📅";
    if (type === "flight") icon = "✈️";
    if (type === "hotel") icon = "🏨";
    if (type === "airport") icon = "🛬";
    if (type === "transport") icon = "🚗";
    if (type === "rest") icon = "🛏️";
    if (type === "home") icon = "🏠";

    const title =
        event.title ||
        event.activity_col ||
        "Travel / Activity";

    let shortText = "";

    /* Location */
    if (event.location_col) {

        shortText += `
            <div class="event-location">
                ${escapeHtml(event.location_col)}
            </div>
        `;

    } else if (event.location) {

        shortText += `
            <div class="event-location">
                ${escapeHtml(event.location)}
            </div>
        `;

    }

    /* Flight details */
    if (type === "flight") {

        if (event.description) {

            shortText += `
                <div class="event-small">
                    ${escapeHtml(
                        event.description
                            .replace(/<br>/gi, " • ")
                    )}
                </div>
            `;

        }

    }

    /* Transport details */
    else if (
        event.transport ||
        event.transport_mode ||
        event.duration
    ) {

        const transport =
            event.transport ||
            event.transport_mode ||
            "";

        const duration =
            event.duration || "";

        const distance =
            event.distance || "";

        shortText += `
            <div class="event-small">
                ${escapeHtml(transport)}
                ${duration ? " • " + escapeHtml(duration) : ""}
                ${distance && distance !== "_"
                    ? " • " + escapeHtml(distance)
                    : ""}
            </div>
        `;

    }

    /* Meeting */
    if (type === "meeting") {

        if (event.description) {

            shortText += `
                <div class="event-small">
                    ${escapeHtml(
                        event.description
                            .replace(/<br>/gi, " • ")
                    )}
                </div>
            `;

        }

    }

    /* Map / booking link */
    let link = "";

    if (event.link) {

        link = `
            <a
                class="map-link"
                href="${safeUrl(event.link)}"
                target="_blank"
                rel="noopener">
                ${event.link_text || "View on Map"}
            </a>
        `;

    } else if (event.maps_url) {

        link = `
            <a
                class="map-link"
                href="${safeUrl(event.maps_url)}"
                target="_blank"
                rel="noopener">
                🗺️ View on Map
            </a>
        `;

    }

    item.innerHTML = `

        <div class="event-time">
            ${escapeHtml(event.time || "—")}
        </div>

        <div class="event-icon">
            ${icon}
        </div>

        <div class="event-content">

            <strong>
                ${escapeHtml(title)}
            </strong>

            ${shortText}

            ${link}

        </div>

    `;

    return item;
}
        // =========================
    // EVENT ICON
    // =========================

    function eventIcon(type) {

        switch (
            String(type || "").toLowerCase()
        ) {

            case "meeting":
                return "🤝";

            case "flight":
                return "✈️";

            case "hotel":
                return "🏨";

            case "airport":
                return "🛫";

            case "transport":
                return "🚗";

            case "rest":
                return "🛏️";

            case "home":
                return "🏠";

            default:
                return "📍";

        }

    }


    // =========================
    // FORMAT DATE
    // =========================

    function formatDate(value) {

        if (!value) {
            return "Date not specified";
        }


        const date =
            new Date(
                value + "T00:00:00"
            );


        if (
            Number.isNaN(
                date.getTime()
            )
        ) {
            return value;
        }


        return date.toLocaleDateString(
            "en-GB",
            {
                weekday: "short",
                day: "2-digit",
                month: "short",
                year: "numeric"
            }
        );

    }


    // =========================
    // ESCAPE HTML
    // =========================

    function escapeHtml(value) {

        return String(
            value ?? ""
        )
            .replace(
                /&/g,
                "&amp;"
            )
            .replace(
                /</g,
                "&lt;"
            )
            .replace(
                />/g,
                "&gt;"
            )
            .replace(
                /"/g,
                "&quot;"
            )
            .replace(
                /'/g,
                "&#039;"
            );

    }


    // =========================
    // SAFE URL
    // =========================

    function safeUrl(value) {

        try {

            const url =
                new URL(
                    value,
                    window.location.origin
                );


            if (
                url.protocol === "http:" ||
                url.protocol === "https:"
            ) {

                return url.href;

            }

        } catch (error) {

            console.log(
                "Invalid URL:",
                error
            );

        }


        return "#";

    }


    // =========================
    // START WITH 3 PARTICIPANTS
    // =========================

    addParticipant();

    addParticipant();

    addParticipant();

});