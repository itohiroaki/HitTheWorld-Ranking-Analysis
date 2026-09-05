/* =========================================================
   HIT : The World
   Ranking Analysis - Ver.6

   構成
   ---------------------------------------------------------
   🏠 概要
   🏆 ランキング
   🔥 今日の動き
   🔍 プレイヤー

   Ver.5のプレイヤー検索・詳細機能を維持
   Ver.6でダッシュボード・総合ランキング・タブ構成を追加
========================================================= */


/* =========================================================
   Data URLs
========================================================= */

const LATEST_DATA_URL =
    "/data/history/daily_analysis_latest.json";

const DAILY_ANALYSIS_DIR =
    "/data/history/daily_analysis";

const DAILY_INDEX_URL =
    `${DAILY_ANALYSIS_DIR}/index.json`;

const PLAYER_HISTORY_URL =
    "/data/history/player_history.json";


/* =========================================================
   Global State
========================================================= */

let currentData = null;
let playerHistoryData = null;
let availableDates = [];
let currentRankingGroup = "Combined";
let currentTodayGroup = "All";
let dashboardServerDistributionData = null;
let dashboardLevelDistributionData = null;
let dashboardGuildDistributionData = null;



/* =========================================================
   Initialization
========================================================= */

document.addEventListener("DOMContentLoaded", () => {
    setupMainTabs();
    setupRankingTabs();
    setupTodayFilters();
    setupLatestButton();
    setupPlayerSearch();
    setupSearchTypeTabs();
    setupPlayerModal();
    loadData();
});


/* =========================================================
   Data Loading
========================================================= */

async function loadData() {

    try {

        const response =
            await fetch(
                `${LATEST_DATA_URL}?t=${Date.now()}`
            );


        if (!response.ok) {

            throw new Error(
                "daily_analysis_latest.jsonを読み込めませんでした"
            );

        }


        currentData =
            await response.json();


        window.latestRankingData =
            currentData;


await loadDateIndex();

await loadPlayerHistory();

setupDateSelector();

        displayData(
            currentData
        );


    } catch (error) {

        console.error(
            "データ読み込みエラー:",
            error
        );


        showError(
            error.message
        );

    }

}


/* =========================================================
   Date Index
========================================================= */

async function loadDateIndex() {

    try {

        const response =
            await fetch(
                `${DAILY_INDEX_URL}?t=${Date.now()}`
            );


        if (!response.ok) {

            throw new Error(
                "index.jsonを読み込めませんでした"
            );

        }


        const data =
            await response.json();


        if (Array.isArray(data)) {

            availableDates =
                data;

        } else if (
            data &&
            Array.isArray(data.dates)
        ) {

            availableDates =
                data.dates;

        } else {

            availableDates = [];

        }


    } catch (error) {

        console.warn(
            "日付一覧の読み込みに失敗:",
            error.message
        );


        if (
            currentData &&
            currentData.date
        ) {

            availableDates = [
                currentData.date
            ];

        } else {

            availableDates = [];

        }

    }

}


/* =========================================================
   Date Selector
========================================================= */

function setupDateSelector() {

    const select =
        document.getElementById(
            "history-date"
        );


    if (!select) {
        return;
    }


    select.innerHTML = "";


    const dates =
        [
            ...new Set(
                availableDates
                    .map(item => {

                        if (
                            typeof item ===
                            "string"
                        ) {

                            return item;

                        }


                        if (
                            item &&
                            item.date
                        ) {

                            return String(
                                item.date
                            );

                        }


                        return null;

                    })
                    .filter(Boolean)
            )
        ];


    dates.sort(
        (a, b) =>
            String(b).localeCompare(
                String(a)
            )
    );


    if (
        currentData &&
        currentData.date &&
        !dates.includes(
            String(currentData.date)
        )
    ) {

        dates.unshift(
            String(currentData.date)
        );

    }


    if (!dates.length) {

        const option =
            document.createElement(
                "option"
            );


        option.value = "";

        option.textContent =
            "データなし";


        select.appendChild(
            option
        );


        return;

    }


    dates.forEach(date => {

        const option =
            document.createElement(
                "option"
            );


        option.value =
            date;


        option.textContent =
            formatDate(date);


        select.appendChild(
            option
        );

    });


    if (
        currentData &&
        currentData.date
    ) {

        select.value =
            String(
                currentData.date
            );

    }


    select.onchange = () => {

        const date =
            select.value;


        if (!date) {
            return;
        }


        loadDailyAnalysis(
            date
        );

    };

}


/* =========================================================
   Latest Button
========================================================= */

function setupLatestButton() {

    const button =
        document.getElementById(
            "latest-button"
        );


    if (!button) {
        return;
    }


    button.addEventListener(
        "click",
        async () => {

            try {

                button.disabled =
                    true;


                button.textContent =
                    "読み込み中...";


                const response =
                    await fetch(
                        `${LATEST_DATA_URL}?t=${Date.now()}`
                    );


                if (!response.ok) {

                    throw new Error(
                        "最新データを読み込めませんでした"
                    );

                }


                currentData =
                    await response.json();


                window.latestRankingData =
                    currentData;


                const select =
                    document.getElementById(
                        "history-date"
                    );


                if (
                    select &&
                    currentData.date
                ) {

                    select.value =
                        String(
                            currentData.date
                        );

                }


                displayData(
                    currentData
                );


            } catch (error) {

                console.error(
                    error
                );


                alert(
                    "最新データの読み込みに失敗しました。\n" +
                    error.message
                );


            } finally {

                button.disabled =
                    false;


                button.textContent =
                    "最新データ";

            }

        }
    );

}


/* =========================================================
   Daily Analysis
========================================================= */

async function loadDailyAnalysis(
    date
) {

    try {

        if (
            currentData &&
            String(currentData.date) ===
            String(date)
        ) {

            displayData(
                currentData
            );

            return;

        }


        const response =
            await fetch(
                `${DAILY_ANALYSIS_DIR}/${date}.json?t=${Date.now()}`
            );


        if (!response.ok) {

            throw new Error(
                `${date}の分析データが見つかりません`
            );

        }


        const data =
            await response.json();


        currentData =
            data;


        window.latestRankingData =
            data;


        displayData(
            data
        );


    } catch (error) {

        console.error(
            error
        );


        alert(
            "履歴データの読み込みに失敗しました。\n" +
            error.message
        );

    }

}


/* =========================================================
   Main Display
========================================================= */

function displayData(
    data
) {

    if (!data) {
        return;
    }


    /*
     * 共通参照
     */
    currentData =
        data;


    window.latestRankingData =
        data;


    /*
     * Header
     */
    displayHeader(
        data
    );


    /*
     * Dashboard
     */
    displayDashboard(
        data
    );


    /*
     * 今日の動き
     */
    displayEventSummary(
        data
    );

    displayRankUp(
        data
    );

    displayRankDown(
        data
    );

    displayEntry(
        data
    );

    displayExit(
        data
    );

    displayLevelUp(
        data
    );


    /*
     * ランキング
     */
    if (
        currentRankingGroup ===
        "Combined"
    ) {

        displayCombinedRanking(
            data
        );

    } else {

        displayCurrentRanking(
            data
        );

    }


    /*
     * 既存統計
     */
    displayStatistics(
        data
    );


    /*
     * プレイヤークリック
     */
    setupPlayerClickableElements();

}


/* =========================================================
   Header
========================================================= */

function displayHeader(
    data
) {

    const updateDate =
        document.getElementById(
            "update-date"
        );


    if (updateDate) {

        updateDate.textContent =
            `データ更新日：${formatDate(data.date)}`;

    }


    const comparisonDate =
        document.getElementById(
            "comparison-date"
        );


    if (!comparisonDate) {
        return;
    }


    if (data.previous_date) {

        comparisonDate.textContent =
            `比較対象：${formatDate(
                data.previous_date
            )}`;

    } else {

        comparisonDate.textContent =
            "比較対象：なし";

    }

}


/* =========================================================
   Main Tabs
========================================================= */

function setupMainTabs() {

    const tabs =
        document.querySelectorAll(
            ".main-tab"
        );


    const pages =
        document.querySelectorAll(
            ".main-page"
        );


    if (
        !tabs.length ||
        !pages.length
    ) {

        return;

    }


    tabs.forEach(tab => {

        tab.addEventListener(
            "click",
            () => {

                const pageName =
                    tab.dataset.page;


                if (!pageName) {
                    return;
                }


                /*
                 * タブ
                 */
                tabs.forEach(item => {

                    item.classList.toggle(
                        "active",
                        item === tab
                    );

                });


                /*
                 * ページ
                 */
                pages.forEach(page => {

                    const target =
                        page.id ===
                        `page-${pageName}`;


                    page.classList.toggle(
                        "active",
                        target
                    );

                });


                /*
                 * 上へ
                 */
                window.scrollTo({
                    top: 0,
                    behavior: "smooth"
                });

            }
        );

    });


    /*
     * 初期ページ
     */
    const activeTab =
        document.querySelector(
            ".main-tab.active"
        );


    if (activeTab) {

        const pageName =
            activeTab.dataset.page;


        pages.forEach(page => {

            page.classList.toggle(
                "active",
                page.id ===
                `page-${pageName}`
            );

        });

    }

}


/* =========================================================
   Event Summary
========================================================= */

function displayEventSummary(data) {

    const date =
        data?.date || "";

    const entry =
        filterTodayEvents(
            data?.rankings?.entry || [],
            date
        );

    const exit =
        filterTodayEvents(
            data?.rankings?.exit || [],
            date
        );

    const rankUp =
        filterTodayEvents(
            data?.rankings?.rank_up || [],
            date
        );

    const rankDown =
        filterTodayEvents(
            data?.rankings?.rank_down || [],
            date
        );

    const levelUp =
        filterTodayEvents(
            data?.rankings?.level_up || [],
            date
        );

const guildChange =
    filterTodayEvents(
        data?.changes?.guild_change || [],
        date
    );

    setText(
        "event-entry",
        entry.length
    );

    setText(
        "event-exit",
        exit.length
    );

    setText(
        "event-rank-up",
        rankUp.length
    );

    setText(
        "event-rank-down",
        rankDown.length
    );

    setText(
        "event-level-up",
        levelUp.length
    );

        setText(
        "event-guild-change",
        guildChange.length
    );


    /* =====================================================
       TOP100入りカード
       クリックで共通キャラ一覧モーダル
    ===================================================== */

    const entryCard =
        document.querySelector(
            ".event-card.event-entry"
        );


    if (entryCard) {

        entryCard.style.cursor =
            "pointer";


        entryCard.onclick =
            () => {

                const players =
                    getUniqueCombinedRanking(
                        data
                    );


                const members =
                    entry
                        .map(
                            event => {

                                const character =
                                    String(
                                        event.character ||
                                        ""
                                    );


                                const currentPlayer =
                                    players.find(
                                        player =>
                                            String(
                                                player.character ||
                                                ""
                                            ) === character
                                    );


                                if (
                                    !currentPlayer
                                ) {
                                    return null;
                                }


                                return {

                                    rank:
                                        currentPlayer.rank,

                                    server:
                                        currentPlayer.server,

                                    character:
                                        currentPlayer.character,

                                    guild:
                                        currentPlayer.guild

                                };

                            }
                        )
                        .filter(
                            player =>
                                player !== null
                        )
                        .sort(
                            (a, b) => {

                                const rankA =
                                    Number(a.rank);

                                const rankB =
                                    Number(b.rank);


                                if (
                                    Number.isFinite(rankA) &&
                                    Number.isFinite(rankB)
                                ) {
                                    return rankA - rankB;
                                }


                                return String(
                                    a.character || ""
                                ).localeCompare(
                                    String(
                                        b.character || ""
                                    ),
                                    "ja"
                                );

                            }
                        );


                openCharacterListModal(
                    "🆕 TOP100入り",
                    `${members.length}人`,
                    members
                );

            };

    }

   /* =====================================================
   圏外カード
   クリックで共通キャラ一覧モーダル
　　===================================================== */

    const exitCard =
      document.querySelector(
        ".event-card.event-exit"
           );


    if (exitCard) {

     exitCard.style.cursor =
        "pointer";


    exitCard.onclick =
        () => {

            const players =
                getUniqueCombinedRanking(
                    data
                );


            const members =
                exit
                    .map(
                        event => {

                            const character =
                                String(
                                    event.character ||
                                    ""
                                );


                            return {
    rank:
        event.old_rank,

    server:
        event.group,

    character:
        event.character,

    guild:
        ""
};

                        }
                    )
                    .filter(
                        player =>
                            player !== null
                    )
                    .sort(
                        (a, b) => {

                            const rankA =
                                Number(a.rank);

                            const rankB =
                                Number(b.rank);


                            if (
                                Number.isFinite(rankA) &&
                                Number.isFinite(rankB)
                            ) {
                                return rankA - rankB;
                            }


                            return String(
                                a.character || ""
                            ).localeCompare(
                                String(
                                    b.character || ""
                                ),
                                "ja"
                            );

                        }
                    );


            openCharacterListModal(
                "🚪 圏外",
                `${members.length}人`,
                members
            );

        };

    } 

    /* =====================================================
   順位上昇カード
   クリックで共通キャラ一覧モーダル
===================================================== */

    const rankUpCard =
    document.querySelector(
        ".event-card.event-rank-up"
    );

    if (rankUpCard) {

    rankUpCard.style.cursor =
        "pointer";

    rankUpCard.onclick =
        () => {

            const players =
                getUniqueCombinedRanking(
                    data
                );

            const members =
                rankUp
                    .map(
                        event => {

                            const character =
                                String(
                                    event.character ||
                                    ""
                                );

                            const currentPlayer =
                                players.find(
                                    player =>
                                        String(
                                            player.character ||
                                            ""
                                        ) === character
                                );

                            if (!currentPlayer) {
                                return null;
                            }

                            return {
                                rank:
                                    currentPlayer.rank,

                                server:
                                    currentPlayer.server,

                                character:
                                    currentPlayer.character,

                                guild:
                                    currentPlayer.guild
                            };
                        }
                    )
                    .filter(
                        player =>
                            player !== null
                    )
                    .sort(
                        (a, b) => {

                            const rankA =
                                Number(a.rank);

                            const rankB =
                                Number(b.rank);

                            if (
                                Number.isFinite(rankA) &&
                                Number.isFinite(rankB)
                            ) {
                                return rankA - rankB;
                            }

                            return String(
                                a.character || ""
                            ).localeCompare(
                                String(
                                    b.character || ""
                                ),
                                "ja"
                            );
                        }
                    );

            openCharacterListModal(
                "📈 順位上昇",
                `${members.length}人`,
                members
            );
        };
    }
    
    /* =====================================================
   順位下降カード
   クリックで共通キャラ一覧モーダル
===================================================== */

const rankDownCard =
    document.querySelector(
        ".event-card.event-rank-down"
    );

if (rankDownCard) {

    rankDownCard.style.cursor =
        "pointer";

    rankDownCard.onclick =
        () => {

            const players =
                getUniqueCombinedRanking(
                    data
                );

            const members =
                rankDown
                    .map(
                        event => {

                            const character =
                                String(
                                    event.character ||
                                    ""
                                );

                            const currentPlayer =
                                players.find(
                                    player =>
                                        String(
                                            player.character ||
                                            ""
                                        ) === character
                                );

                            if (!currentPlayer) {
                                return null;
                            }

                            return {
                                rank:
                                    currentPlayer.rank,

                                server:
                                    currentPlayer.server,

                                character:
                                    currentPlayer.character,

                                guild:
                                    currentPlayer.guild
                            };
                        }
                    )
                    .filter(
                        player =>
                            player !== null
                    )
                    .sort(
                        (a, b) => {

                            const rankA =
                                Number(a.rank);

                            const rankB =
                                Number(b.rank);

                            if (
                                Number.isFinite(rankA) &&
                                Number.isFinite(rankB)
                            ) {
                                return rankA - rankB;
                            }

                            return String(
                                a.character || ""
                            ).localeCompare(
                                String(
                                    b.character || ""
                                ),
                                "ja"
                            );
                        }
                    );

            openCharacterListModal(
                "📉 順位下降",
                `${members.length}人`,
                members
            );
        };
    }

    /* =====================================================
   レベルアップカード
   クリックで共通キャラ一覧モーダル
===================================================== */

const levelUpCard =
    document.querySelector(
        ".event-card.event-level-up"
    );

if (levelUpCard) {

    levelUpCard.style.cursor =
        "pointer";

    levelUpCard.onclick =
        () => {

            const players =
                getUniqueCombinedRanking(
                    data
                );

            const members =
                levelUp
                    .map(
                        event => {

                            const character =
                                String(
                                    event.character ||
                                    ""
                                );

                            const currentPlayer =
                                players.find(
                                    player =>
                                        String(
                                            player.character ||
                                            ""
                                        ) === character
                                );

                            if (!currentPlayer) {
                                return null;
                            }

                            return {
                                rank:
                                    currentPlayer.rank,

                                server:
                                    currentPlayer.server,

                                character:
                                    currentPlayer.character,

                                guild:
                                    currentPlayer.guild
                            };
                        }
                    )
                    .filter(
                        player =>
                            player !== null
                    )
                    .sort(
                        (a, b) => {

                            const rankA =
                                Number(a.rank);

                            const rankB =
                                Number(b.rank);

                            if (
                                Number.isFinite(rankA) &&
                                Number.isFinite(rankB)
                            ) {
                                return rankA - rankB;
                            }

                            return String(
                                a.character || ""
                            ).localeCompare(
                                String(
                                    b.character || ""
                                ),
                                "ja"
                            );
                        }
                    );

            openCharacterListModal(
                "🆙 レベルアップ",
                `${members.length}人`,
                members
            );
        };
    }

    /* =====================================================
   ギルド変更カード
   クリックで共通キャラ一覧モーダル
===================================================== */

const guildChangeCard =
    document.querySelector(
        ".event-card.event-guild"
    );

if (guildChangeCard) {

    guildChangeCard.style.cursor =
        "pointer";

    guildChangeCard.onclick =
        () => {

            const players =
                getUniqueCombinedRanking(
                    data
                );

            const members =
                guildChange
                    .map(
                        event => {

                            const character =
                                String(
                                    event.character ||
                                    ""
                                );

                            const currentPlayer =
                                players.find(
                                    player =>
                                        String(
                                            player.character ||
                                            ""
                                        ) === character
                                );

                            if (!currentPlayer) {
                                return null;
                            }

                            return {
                                rank:
                                    currentPlayer.rank,

                                server:
                                    currentPlayer.server,

                                character:
                                    currentPlayer.character,

                                guild:
                                    currentPlayer.guild
                            };
                        }
                    )
                    .filter(
                        player =>
                            player !== null
                    )
                    .sort(
                        (a, b) => {

                            const rankA =
                                Number(a.rank);

                            const rankB =
                                Number(b.rank);

                            if (
                                Number.isFinite(rankA) &&
                                Number.isFinite(rankB)
                            ) {
                                return rankA - rankB;
                            }

                            return String(
                                a.character || ""
                            ).localeCompare(
                                String(
                                    b.character || ""
                                ),
                                "ja"
                            );
                        }
                    );

            openCharacterListModal(
                "⚔️ ギルド変更",
                `${members.length}人`,
                members
            );
        };
    }

}

/* =========================================================
   Rank Up
========================================================= */

function displayRankUp(
    data
) {

    const list =
        filterTodayEvents(
            data?.rankings?.rank_up || [],
            data?.date
        );


    const container =
        document.getElementById(
            "rank-up-list"
        );


    if (!container) {
        return;
    }


    const top10 =
        list.slice(
            0,
            10
        );


    if (!top10.length) {

        container.innerHTML =
            emptyMessage(
                "順位上昇はありません"
            );


        return;

    }


    container.innerHTML =
        top10
            .map(
                (item, index) =>
                    createRankChangeRow(
                        item,
                        index + 1,
                        "up"
                    )
            )
            .join("");


    setupPlayerClickableElements();

}

/* =========================================================
   Rank Down
========================================================= */

function displayRankDown(
    data
) {

const list =
    filterTodayEvents(
        data?.rankings?.rank_down || [],
        data?.date
    );


    const container =
        document.getElementById(
            "rank-down-list"
        );


    if (!container) {
        return;
    }


    const top10 =
        list.slice(
            0,
            10
        );


    if (!top10.length) {

        container.innerHTML =
            emptyMessage(
                "順位下降はありません"
            );


        return;

    }


    container.innerHTML =
        top10
            .map(
                (item, index) =>
                    createRankChangeRow(
                        item,
                        index + 1,
                        "down"
                    )
            )
            .join("");


    setupPlayerClickableElements();

}


/* =========================================================
   Rank Change Row
========================================================= */

function createRankChangeRow(
    item,
    number,
    direction
) {

    const oldRank =
        toNumber(
            item.old_rank
        );


    const newRank =
        toNumber(
            item.new_rank
        );


    const change =
        toNumber(
            item.change
        );


    const group =
        item.group || "";


    const character =
        item.character ||
        "不明";


    const sign =
        direction === "up"
            ? "+"
            : "-";


    const changeValue =
        Math.abs(
            change
        );


    return `

        <div class="change-row">

            <div class="change-rank">
                ${number}
            </div>


            <div class="change-player">

                <div
                    class="change-character player-clickable"
                    data-character="${escapeHtml(
                        character
                    )}"
                >
                    ${escapeHtml(
                        character
                    )}
                </div>


                <div class="change-meta">
                    ${escapeHtml(
                        group
                    )}
                </div>

            </div>


            <div class="change-rank-value">

                <span class="old-rank">
                    ${oldRank}
                </span>

                <span class="rank-arrow">
                    →
                </span>

                <span class="new-rank">
                    ${newRank}
                </span>

                <span class="rank-difference ${direction}">
                    ${sign}${changeValue}
                </span>

            </div>

        </div>

    `;

}


/* =========================================================
   Entry
========================================================= */

function displayEntry(
    data
) {

 const list =
    filterTodayEvents(
        data?.rankings?.entry || [],
        data?.date
    );


    const container =
        document.getElementById(
            "entry-list"
        );


    if (!container) {
        return;
    }


    if (!list.length) {

        container.innerHTML =
            emptyMessage(
                "TOP100入りはありません"
            );


        return;

    }


    container.innerHTML =
        list
            .map(
                (item, index) =>
                    createEntryRow(
                        item,
                        index + 1
                    )
            )
            .join("");


    setupPlayerClickableElements();

}


/* =========================================================
   Entry Row
========================================================= */

function createEntryRow(
    item,
    number
) {

    const character =
        item.character ||
        "不明";


    const group =
        item.group ||
        "";


    const newRank =
        toNumber(
            item.new_rank
        );


    const firstObservation =
        item.first_observation ===
        true;


    return `

        <div class="compact-row">

            <div class="compact-number">
                ${number}
            </div>


            <div
                class="compact-character player-clickable"
                data-character="${escapeHtml(
                    character
                )}"
            >

                ${escapeHtml(
                    character
                )}

                ${
                    firstObservation
                        ? `
                            <span class="first-observation">
                                初観測
                            </span>
                          `
                        : ""
                }

            </div>


            <div class="compact-meta">

                ${escapeHtml(
                    group
                )}

                ${
                    newRank
                        ? ` ${newRank}位`
                        : ""
                }

            </div>

        </div>

    `;

}


/* =========================================================
   Exit
========================================================= */

function displayExit(
    data
) {

const list =
    filterTodayEvents(
        data?.rankings?.exit || [],
        data?.date
    );


    const container =
        document.getElementById(
            "exit-list"
        );


    if (!container) {
        return;
    }


    if (!list.length) {

        container.innerHTML =
            emptyMessage(
                "圏外になったプレイヤーはいません"
            );


        return;

    }


    container.innerHTML =
        list
            .map(
                (item, index) =>
                    createExitRow(
                        item,
                        index + 1
                    )
            )
            .join("");


    setupPlayerClickableElements();

}


/* =========================================================
   Exit Row
========================================================= */

function createExitRow(
    item,
    number
) {

    const character =
        item.character ||
        "不明";


    const group =
        item.group ||
        "";


    const oldRank =
        toNumber(
            item.old_rank
        );


    return `

        <div class="compact-row">

            <div class="compact-number">
                ${number}
            </div>


            <div
                class="compact-character player-clickable"
                data-character="${escapeHtml(
                    character
                )}"
            >
                ${escapeHtml(
                    character
                )}
            </div>


            <div class="compact-meta">

                ${escapeHtml(
                    group
                )}

                ${
                    oldRank
                        ? ` ${oldRank}位`
                        : ""
                }

                → 圏外

            </div>

        </div>

    `;

}


/* =========================================================
   Level Up
========================================================= */

function displayLevelUp(
    data
) {

const list =
    filterTodayEvents(
        data?.rankings?.level_up || [],
        data?.date
    );


    const container =
        document.getElementById(
            "level-up-list"
        );


    if (!container) {
        return;
    }


    if (!list.length) {

        container.innerHTML =
            emptyMessage(
                "レベルアップはありません"
            );


        return;

    }


    container.innerHTML =
        list
            .map(
                (item, index) =>
                    createLevelChangeRow(
                        item,
                        index + 1
                    )
            )
            .join("");


    setupPlayerClickableElements();

}


/* =========================================================
   Level Change Row
========================================================= */

function createLevelChangeRow(
    item,
    number
) {

    const character =
        item.character ||
        "不明";


    const group =
        item.group ||
        "";


    const oldLevel =
        toNumber(
            item.old_level
        );


    const newLevel =
        toNumber(
            item.new_level
        );


    const change =
        toNumber(
            item.change
        );


    return `

        <div class="level-change-row">

            <div class="level-change-number">
                ${number}
            </div>


            <div>

                <div
                    class="level-change-character player-clickable"
                    data-character="${escapeHtml(
                        character
                    )}"
                >
                    ${escapeHtml(
                        character
                    )}
                </div>


                <div class="level-change-meta">
                    ${escapeHtml(
                        group
                    )}
                </div>

            </div>


            <div class="level-values">

                <span class="old-level">
                    Lv${oldLevel}
                </span>


                <span class="level-arrow">
                    →
                </span>


                <span class="new-level">
                    Lv${newLevel}
                </span>


                ${
                    change
                        ? `
                            <span class="level-difference">
                                +${change}
                            </span>
                          `
                        : ""
                }

            </div>

        </div>

    `;

}


/* =========================================================
   Ranking Tabs
========================================================= */

function setupRankingTabs() {

    const tabs =
        document.querySelectorAll(
            ".ranking-tab"
        );


    if (!tabs.length) {
        return;
    }


    tabs.forEach(tab => {

        tab.addEventListener(
            "click",
            () => {

                const group =
                    tab.dataset.group;


                if (!group) {
                    return;
                }


                currentRankingGroup =
                    group;


                tabs.forEach(item => {

                    item.classList.toggle(
                        "active",
                        item === tab
                    );

                });


                if (!currentData) {
                    return;
                }


                if (
                    group ===
                    "Combined"
                ) {

                    displayCombinedRanking(
                        currentData
                    );

                } else {

                    displayCurrentRanking(
                        currentData
                    );

                }

            }
        );

    });

}

/* =========================================================
   Today Filters
========================================================= */

function setupTodayFilters() {

    const filters =
        document.querySelectorAll(".today-filter");

    if (!filters.length) {
        return;
    }

    filters.forEach(filter => {

        filter.addEventListener("click", () => {

            const group =
                filter.dataset.todayGroup;

            if (!group) {
                return;
            }

            currentTodayGroup = group;

            filters.forEach(item => {
                item.classList.toggle(
                    "active",
                    item === filter
                );
            });

            if (!currentData) {
                return;
            }

            displayEventSummary(currentData);
            displayRankUp(currentData);
            displayRankDown(currentData);
            displayEntry(currentData);
            displayExit(currentData);
            displayLevelUp(currentData);

        });

    });

}

/* =========================================================
   Today Event Server Filter
========================================================= */

function getEventServer(event, date) {

    if (!event || !date || !playerHistoryData) {
        return "";
    }

    const character =
        String(event.character || "").trim();

    if (!character) {
        return "";
    }

    const players =
        getPlayerArray(playerHistoryData);

    const player =
        players.find(
            item =>
                String(item.character || "").trim()
                === character
        );

    if (!player) {
        return "";
    }

    const history =
        Array.isArray(player.history)
            ? player.history
            : [];

    const record =
        history.find(
            item =>
                String(item.date || "") ===
                String(date)
        );

    if (!record) {
        return "";
    }

    /*
     * Eda / Virba の当日データを確認
     */
const serverRanking =
    record.server_ranking || {};

const group =
    String(
        event.group || ""
    ).trim();

const ranking =
    serverRanking[group] || {};


if (
    ranking.visible &&
    ranking.server
) {
    return String(
        ranking.server
    ).trim();
}


return "";

}

function filterTodayEvents(
    events,
    date
) {

    if (!Array.isArray(events)) {
        return [];
    }

    if (currentTodayGroup === "All") {
        return events;
    }


    return events.filter(event => {

        const eventGroup =
            String(
                event.group || ""
            ).trim();


        /*
         * Eda / Virba
         */
        if (
            currentTodayGroup === "Eda" ||
            currentTodayGroup === "Virba"
        ) {

            return (
                eventGroup ===
                currentTodayGroup
            );

        }


        /*
         * Eda1～4 / Virba1～4
         */
        const server =
            getEventServer(
                event,
                date
            );

        return (
            server ===
            currentTodayGroup
        );

    });

}


/* =========================================================
   Current Ranking
========================================================= */

function displayCurrentRanking(
    data
) {

    const rankings =
        data?.current_ranking || {};

    let list = [];


    /*
     * Eda / Virba 全体
     */
    if (
        currentRankingGroup === "Eda" ||
        currentRankingGroup === "Virba"
    ) {

        list =
            Array.isArray(
                rankings[currentRankingGroup]
            )
                ? rankings[currentRankingGroup]
                : [];

    }


    /*
     * Eda1～Eda4 / Virba1～Virba4
     */
    else if (
        /^Eda[1-4]$/.test(currentRankingGroup) ||
        /^Virba[1-4]$/.test(currentRankingGroup)
    ) {

        const baseGroup =
            currentRankingGroup.startsWith("Eda")
                ? "Eda"
                : "Virba";


        const baseList =
            Array.isArray(
                rankings[baseGroup]
            )
                ? rankings[baseGroup]
                : [];


        list =
            baseList.filter(
                item =>
                    String(
                        item.server || ""
                    ).trim()
                    === currentRankingGroup
            );

    }


    /*
     * ランキング一覧
     */
    else if (
        currentRankingGroup === "Combined"
    ) {

        displayCombinedRanking(data);

        return;

    }


    const container =
        document.getElementById(
            "current-ranking-list"
        );


    if (!container) {
        return;
    }


    const groupName =
        document.getElementById(
            "ranking-group-name"
        );


    const total =
        document.getElementById(
            "ranking-total"
        );


    if (groupName) {

        groupName.textContent =
            currentRankingGroup;

    }


    if (total) {

        total.textContent =
            `${list.length}人`;

    }


    /*
     * Eda / Virba の人数表示
     */
    updateRankingCounts(
        rankings
    );


    /*
     * データなし
     */
    if (!list.length) {

        container.innerHTML =
            emptyMessage(
                "ランキングデータがありません"
            );

        return;

    }


    /*
     * ランキング表示
     */
    container.innerHTML = `

        <div class="ranking-table-header">

            <div>順位</div>
            <div>キャラクター</div>
            <div>Lv</div>
            <div>サーバー</div>
            <div>ギルド</div>
            <div></div>

        </div>


        ${
            list
                .map(
                    item =>
                        createRankingRow(
                            item
                        )
                )
                .join("")
        }

    `;


    setupPlayerClickableElements();

}

/* =========================================================
   Ranking Counts
========================================================= */

function updateRankingCounts(
    rankings
) {

    const eda =
        document.getElementById(
            "ranking-count-eda"
        );


    const virba =
        document.getElementById(
            "ranking-count-virba"
        );


    if (eda) {

        eda.textContent =
            Array.isArray(
                rankings.Eda
            )
                ? rankings.Eda.length
                : 0;

    }


    if (virba) {

        virba.textContent =
            Array.isArray(
                rankings.Virba
            )
                ? rankings.Virba.length
                : 0;

    }

}


/* =========================================================
   Ranking Row
========================================================= */

function createRankingRow(
    item
) {

    const rank =
        toNumber(
            item.rank
        );


    const level =
        toNumber(
            item.level
        );


    const character =
        item.character ||
        "不明";


    const server =
        item.server ||
        "";


    const guild =
        item.guild ||
        "";


    const topThree =
        rank >= 1 &&
        rank <= 3
            ? "top-three"
            : "";


    return `

        <div class="ranking-row">

            <div class="ranking-number ${topThree}">
                ${rank || "-"}
            </div>


            <div
                class="ranking-character player-clickable"
                data-character="${escapeHtml(
                    character
                )}"
                title="クリックしてプレイヤー詳細を見る"
            >
                ${escapeHtml(
                    character
                )}
            </div>


            <div class="ranking-level">
                Lv${level || "-"}
            </div>


            <div class="ranking-server">
                ${escapeHtml(
                    server
                )}
            </div>


            <div class="ranking-guild">
                ${escapeHtml(
                    guild ||
                    "無所属"
                )}
            </div>


            <div></div>

        </div>

    `;

}


/* =========================================================
   Combined Ranking
========================================================= */

function displayCombinedRanking(
    data
) {

    const container =
        document.getElementById(
            "current-ranking-list"
        );


    if (!container) {
        return;
    }


    const players =
        getUniqueCombinedRanking(
            data
        );


    /*
     * 総合ランキング
     *
     * ① Lv降順
     * ② サーバー内順位昇順
     * ③ キャラクター名
     */
    players.sort(
        (a, b) => {

            const levelA =
                getPlayerLevel(a) ??
                -1;


            const levelB =
                getPlayerLevel(b) ??
                -1;


            if (
                levelA !==
                levelB
            ) {

                return (
                    levelB -
                    levelA
                );

            }


            const rankA =
                Number(
                    a.rank
                );


            const rankB =
                Number(
                    b.rank
                );


            if (
                Number.isFinite(
                    rankA
                ) &&
                Number.isFinite(
                    rankB
                ) &&
                rankA !== rankB
            ) {

                return (
                    rankA -
                    rankB
                );

            }


            const nameA =
                String(
                    a.character ??
                    ""
                );


            const nameB =
                String(
                    b.character ??
                    ""
                );


            return nameA.localeCompare(
                nameB,
                "ja"
            );

        }
    );


    const groupName =
        document.getElementById(
            "ranking-group-name"
        );


    const total =
        document.getElementById(
            "ranking-total"
        );


    if (groupName) {

        groupName.textContent =
            "総合";

    }


    if (total) {

        total.textContent =
            `${players.length}人`;

    }


    if (!players.length) {

        container.innerHTML =
            emptyMessage(
                "ランキングデータがありません"
            );


        return;

    }


    container.innerHTML = `

        <div class="ranking-table-header">

            <div>総合</div>
            <div>キャラクター</div>
            <div>Lv</div>
            <div>サーバー</div>
            <div>ギルド</div>
            <div>元順位</div>

        </div>


        ${
            players
                .map(
                    (player, index) => {

                        const character =
                            String(
                                player.character ??
                                ""
                            );


                        const level =
                            getPlayerLevel(
                                player
                            );


                        const server =
                            String(
                                player.server ??
                                "-"
                            );


                        const guild =
                            String(
                                player.guild ??
                                "無所属"
                            );


                        const group =
                            String(
                                player.group ??
                                "-"
                            );


                        const rank =
                            Number(
                                player.rank
                            );


                        const topThree =
                            index < 3
                                ? "top-three"
                                : "";


                        return `

                            <div
                                class="ranking-row player-clickable"
                                data-character="${escapeHtml(
                                    character
                                )}"
                            >

                                <div class="ranking-number ${topThree}">
                                    ${index + 1}
                                </div>


                                <div class="ranking-character">

                                    <strong>
                                        ${escapeHtml(
                                            character
                                        )}
                                    </strong>

                                </div>


                                <div class="ranking-level">

                                    ${
                                        level !== null
                                            ? `Lv${level}`
                                            : "-"
                                    }

                                </div>


                                <div class="ranking-server">
                                    ${escapeHtml(
                                        server
                                    )}
                                </div>


                                <div class="ranking-guild">
                                    ${escapeHtml(
                                        guild
                                    )}
                                </div>


                                <div class="ranking-original-rank">

                                    ${
                                        group !== "-" &&
                                        Number.isFinite(rank)
                                            ? `
                                                ${escapeHtml(
                                                    group
                                                )}
                                                ${rank}位
                                              `
                                            : "-"
                                    }

                                </div>

                            </div>

                        `;

                    }
                )
                .join("")
        }

    `;


    setupPlayerClickableElements();

}


/* =========================================================
   Combined Players
========================================================= */

function getCombinedCurrentRanking(
    data
) {

    const eda =
        Array.isArray(
            data?.current_ranking?.Eda
        )
            ? data.current_ranking.Eda
            : [];


    const virba =
        Array.isArray(
            data?.current_ranking?.Virba
        )
            ? data.current_ranking.Virba
            : [];


    return [

        ...eda.map(
            player => ({
                ...player,
                group: "Eda"
            })
        ),

        ...virba.map(
            player => ({
                ...player,
                group: "Virba"
            })
        )

    ];

}


/* =========================================================
   Unique Combined Players
========================================================= */

function getUniqueCombinedRanking(
    data
) {

    const players =
        getCombinedCurrentRanking(
            data
        );


    const map =
        new Map();


    players.forEach(player => {

        const character =
            String(
                player.character ??
                player.name ??
                ""
            ).trim();


        if (!character) {
            return;
        }


        if (
            !map.has(
                character
            )
        ) {

            map.set(
                character,
                player
            );

        }

    });


    return Array.from(
        map.values()
    );

}


/* =========================================================
   Player Level
========================================================= */

function getPlayerLevel(
    player
) {

    const level =
        Number(
            player.level
        );


    return Number.isFinite(
        level
    )
        ? level
        : null;

}


/* =========================================================
   Dashboard
========================================================= */

function displayDashboard(
    data
) {

    displayDashboardOverview(
        data
    );


    displayDashboardLevelDistribution(
        data
    );


    displayDashboardServerDistribution(
        data
    );

    displayDashboardGuildDistribution(data);


    displayDashboardHighlights(
        data
    );

}

/* =========================================================
   Dashboard Overview
========================================================= */

function displayDashboardOverview(
    data
) {

    const players =
        getUniqueCombinedRanking(
            data
        );


    const levels =
        players
            .map(
                getPlayerLevel
            )
            .filter(
                level =>
                    level !== null
            );


    const playerCount =
        document.getElementById(
            "dashboard-player-count"
        );


    const maxLevel =
        document.getElementById(
            "dashboard-max-level"
        );


    const averageLevel =
        document.getElementById(
            "dashboard-average-level"
        );


    const minLevel =
        document.getElementById(
            "dashboard-min-level"
        );


    const modeLevel =
        document.getElementById(
            "dashboard-mode-level"
        );


    const modeLevelCount =
        document.getElementById(
            "dashboard-mode-level-count"
        );


    if (playerCount) {

        playerCount.textContent =
            String(
                players.length
            );

    }


    if (!levels.length) {

        if (maxLevel) {
            maxLevel.textContent =
                "-";
        }


        if (averageLevel) {
            averageLevel.textContent =
                "-";
        }


        if (minLevel) {
            minLevel.textContent =
                "-";
        }


        if (modeLevel) {
            modeLevel.textContent =
                "-";
        }


        if (modeLevelCount) {
            modeLevelCount.textContent =
                "-";
        }


        return;

    }


    const max =
        Math.max(
            ...levels
        );


    const min =
        Math.min(
            ...levels
        );


    const average =
        levels.reduce(
            (sum, level) =>
                sum + level,
            0
        ) /
        levels.length;


    /*
     * 最頻値
     */
    const levelCounts =
        new Map();


    levels.forEach(level => {

        levelCounts.set(
            level,
            (
                levelCounts.get(
                    level
                ) || 0
            ) + 1
        );

    });


    const mode =
        Array.from(
            levelCounts.entries()
        )
        .sort(
            (a, b) => {

                if (
                    b[1] !==
                    a[1]
                ) {

                    return (
                        b[1] -
                        a[1]
                    );

                }


                return (
                    b[0] -
                    a[0]
                );

            }
        )[0];


    if (maxLevel) {

        maxLevel.textContent =
            `Lv${max}`;

    }


    if (averageLevel) {

        averageLevel.textContent =
            `Lv${average.toFixed(1)}`;

    }


    if (minLevel) {

        minLevel.textContent =
            `Lv${min}`;

    }


    if (modeLevel) {

        modeLevel.textContent =
            `Lv${mode[0]}`;

    }


    if (modeLevelCount) {

        modeLevelCount.textContent =
            `${mode[1]}人`;

    }

}


/* =========================================================
   Dashboard Level Distribution
========================================================= */

function displayDashboardLevelDistribution(
    data
) {

dashboardLevelDistributionData = data;

    const container =
        document.getElementById(
            "dashboard-level-distribution"
        );


    if (!container) {
        return;
    }


    const players =
        getUniqueCombinedRanking(
            data
        );


    const counts =
        new Map();


    players.forEach(player => {

        const level =
            getPlayerLevel(
                player
            );


        if (level === null) {
            return;
        }


        counts.set(
            level,
            (
                counts.get(
                    level
                ) || 0
            ) + 1
        );

    });


    if (!counts.size) {

        container.innerHTML =
            `
                <div class="empty-state">
                    データがありません
                </div>
            `;


        return;

    }


    const sorted =
        Array.from(
            counts.entries()
        )
        .sort(
            (a, b) =>
                b[0] - a[0]
        );


    const maxCount =
        Math.max(
            ...sorted.map(
                item =>
                    item[1]
            )
        );


    container.innerHTML =
        sorted
            .map(
                ([level, count]) => {

                    const percentage =
                        maxCount > 0
                            ? (
                                count /
                                maxCount *
                                100
                            )
                            : 0;


                    return `

                        <div class="dashboard-bar-row">

                            <button
    type="button"
    class="dashboard-bar-label dashboard-level-button"
    data-level="${escapeHtml(
        String(level)
    )}"
>
    Lv${escapeHtml(
        String(level)
    )}
</button>


                            <div class="dashboard-bar-track">

                                <div
                                    class="dashboard-bar-fill"
                                    style="width:${percentage}%"
                                ></div>

                            </div>


                            <div class="dashboard-bar-value">
                                ${count}人
                            </div>

                        </div>

                    `;

                }
            )
            .join("");

    setupDashboardLevelButtons();


}

/* =========================================================
   Dashboard Server Distribution
   + Major Guilds
========================================================= */

function displayDashboardServerDistribution(
    data
) {

    dashboardServerDistributionData = data;

    const container =
        document.getElementById(
            "dashboard-server-distribution"
        );


    if (!container) {
        return;
    }


    const players =
        getUniqueCombinedRanking(
            data
        );


    const serverGroups =
        new Map();


    players.forEach(
        player => {

            const server =
                String(
                    player.server ??
                    ""
                ).trim();


            const guild =
                String(
                    player.guild ??
                    ""
                ).trim();


            if (!server) {
                return;
            }


            if (
                !serverGroups.has(
                    server
                )
            ) {

                serverGroups.set(
                    server,
                    {
                        count: 0,
                        guilds: new Map()
                    }
                );

            }


            const serverData =
                serverGroups.get(
                    server
                );


            serverData.count += 1;


            if (guild) {

                serverData.guilds.set(
                    guild,
                    (
                        serverData.guilds.get(
                            guild
                        ) || 0
                    ) + 1
                );

            }

        }
    );


    const serverOrder = [

        "Eda1",
        "Eda2",
        "Eda3",
        "Eda4",

        "Virba1",
        "Virba2",
        "Virba3",
        "Virba4"

    ];


    const sorted =
        serverOrder
            .filter(
                server =>
                    serverGroups.has(
                        server
                    )
            )
            .map(
                server => [
                    server,
                    serverGroups.get(
                        server
                    )
                ]
            );


    if (!sorted.length) {

        container.innerHTML =
            `
                <div class="empty-state">
                    データがありません
                </div>
            `;


        return;

    }


    const maxCount =
        Math.max(
            ...sorted.map(
                item =>
                    item[1].count
            )
        );


    container.innerHTML =
        sorted
            .map(
                ([server, serverData]) => {

                    const percentage =
                        maxCount > 0
                            ? (
                                serverData.count /
                                maxCount *
                                100
                            )
                            : 0;


                    /* -----------------------------------------
                       主要ギルド TOP5
                    ----------------------------------------- */

                    const guilds =
                        Array.from(
                            serverData.guilds.entries()
                        )
                        .sort(
                            (a, b) => {

                                if (
                                    b[1] !==
                                    a[1]
                                ) {

                                    return (
                                        b[1] -
                                        a[1]
                                    );

                                }


                                return a[0].localeCompare(
                                    b[0],
                                    "ja"
                                );

                            }
                        )
                        .slice(
                            0,
                            5
                        );


                   const guildHtml =
    guilds.length
        ? guilds
            .map(
                ([guild, count]) => `
                    <button
                        type="button"
                        class="dashboard-server-guild"
                        data-server="${escapeHtml(server)}"
                        data-guild="${escapeHtml(guild)}"
                    >
                        ${escapeHtml(guild)}
                        <span class="dashboard-server-guild-count">
                            ${count}人
                        </span>
                    </button>
                `
            )
            .join("")
        : "";


                    return `

                        <div class="dashboard-server-row">

                            <div class="dashboard-bar-row">

                                <div class="dashboard-bar-label">
                                    ${escapeHtml(
                                        server
                                    )}
                                </div>


                                <div class="dashboard-bar-track">

                                    <div
                                        class="dashboard-bar-fill"
                                        style="width:${percentage}%"
                                    ></div>

                                </div>


                                <div class="dashboard-bar-value">
                                    ${serverData.count}人
                                </div>

                            </div>


                            ${
                                guildHtml
                                    ? `

                                        <div class="dashboard-server-guilds-inline">

                                            ${guildHtml}

                                        </div>

                                    `
                                    : ""
                            }

                        </div>

                    `;

                }
            )
            .join("");

setupDashboardGuildButtons();

}

/* =========================================================
   Dashboard Guild Distribution
========================================================= */

function displayDashboardGuildDistribution(data) {

    const container =
        document.getElementById(
            "dashboard-guild-distribution"
        );

    if (!container) {
        return;
    }

    const players =
        getUniqueCombinedRanking(
            data
        );

    dashboardGuildDistributionData =
        players;

    const guildCounts = {};

    players.forEach(player => {

        const guild =
            String(
                player.guild || ""
            ).trim();

        const guildName =
            guild || "無所属";

        guildCounts[guildName] =
            (guildCounts[guildName] || 0) + 1;

    });

    const entries =
        Object.entries(
            guildCounts
        )
        .sort(
            (a, b) =>
                b[1] - a[1] ||
                a[0].localeCompare(
                    b[0],
                    "ja"
                )
        );

    const maxCount =
        entries.length
            ? entries[0][1]
            : 0;

    container.innerHTML =
        entries
            .map(
                ([guild, count]) => {

                    const width =
                        maxCount > 0
                            ? (count / maxCount) * 100
                            : 0;

                    return `
                        <div
    class="dashboard-bar-row dashboard-guild-distribution-button"
    data-guild="${escapeHtml(guild)}"
>

                            <div class="dashboard-bar-label">
                                ${escapeHtml(guild)}
                            </div>

                            <div class="dashboard-bar-track">

                                <div
                                    class="dashboard-bar-fill"
                                    style="width:${width}%"
                                ></div>

                            </div>

                            <div class="dashboard-bar-value">
                                ${count}人
                            </div>

                        </div>
                    `;
                }
            )
            .join("");

    setupDashboardGuildDistributionButtons();

}


function setupDashboardGuildDistributionButtons() {

    const buttons =
        document.querySelectorAll(
            ".dashboard-guild-distribution-button"
        );

    buttons.forEach(button => {

        button.style.cursor =
            "pointer";

        button.addEventListener(
            "click",
            () => {

                const guild =
                    button.dataset.guild || "";

                if (
                    !dashboardGuildDistributionData
                ) {
                    return;
                }

                const members =
                    dashboardGuildDistributionData
                        .filter(
                            player => {

                                const playerGuild =
                                    String(
                                        player.guild || ""
                                    ).trim() || "無所属";

                                return (
                                    playerGuild ===
                                    guild
                                );
                            }
                        )
                        .sort(
                            (a, b) => {

                                const rankA =
                                    Number(a.rank);

                                const rankB =
                                    Number(b.rank);

                                if (
                                    Number.isFinite(rankA) &&
                                    Number.isFinite(rankB)
                                ) {
                                    return (
                                        rankA -
                                        rankB
                                    );
                                }

                                return String(
                                    a.character || ""
                                ).localeCompare(
                                    String(
                                        b.character || ""
                                    ),
                                    "ja"
                                );
                            }
                        );

                openCharacterListModal(
                    `🏰 ${guild}`,
                    `${members.length}人`,
                    members
                );

            }
        );

    });

}

/* =========================================================
   Dashboard Highlights
========================================================= */

function displayDashboardHighlights(
    data
) {

    const container =
        document.getElementById(
            "dashboard-highlights"
        );


    if (!container) {
        return;
    }


    const summary =
        data?.event_summary ??
        data?.events ??
        {};


    const levelUpCount =
        Number(
            summary.level_up ??
            summary.levelUp ??
            0
        );


    const rankUpCount =
        Number(
            summary.rank_up ??
            summary.rankUp ??
            0
        );


    const rankDownCount =
        Number(
            summary.rank_down ??
            summary.rankDown ??
            0
        );


    container.innerHTML = `

        <div class="dashboard-highlight-grid">

            <div class="dashboard-highlight-card">

                <div class="dashboard-highlight-icon">
                    🆙
                </div>


                <div>

                    <div class="dashboard-highlight-label">
                        本日のLv UP
                    </div>


                    <div class="dashboard-highlight-value">
                        ${
                            Number.isFinite(
                                levelUpCount
                            )
                                ? levelUpCount
                                : 0
                        }人
                    </div>

                </div>

            </div>


            <div class="dashboard-highlight-card">

                <div class="dashboard-highlight-icon">
                    📈
                </div>


                <div>

                    <div class="dashboard-highlight-label">
                        順位上昇
                    </div>


                    <div class="dashboard-highlight-value">
                        ${
                            Number.isFinite(
                                rankUpCount
                            )
                                ? rankUpCount
                                : 0
                        }人
                    </div>

                </div>

            </div>


            <div class="dashboard-highlight-card">

                <div class="dashboard-highlight-icon">
                    📉
                </div>


                <div>

                    <div class="dashboard-highlight-label">
                        順位下降
                    </div>


                    <div class="dashboard-highlight-value">
                        ${
                            Number.isFinite(
                                rankDownCount
                            )
                                ? rankDownCount
                                : 0
                        }人
                    </div>

                </div>

            </div>

        </div>

    `;

setupDashboardHighlightButtons();    

}


/* =========================================================
   Statistics
========================================================= */

function displayStatistics(
    data
) {

    const statistics =
        data?.statistics || {};


    displayLevelDistribution(
        statistics.level_distribution ||
        {}
    );


    displayServerDistribution(
        statistics.server_distribution ||
        {}
    );


    displayGuildDistribution(
        statistics.guild_distribution ||
        {}
    );

}


/* =========================================================
   Level Distribution
========================================================= */

function displayLevelDistribution(
    distribution
) {

    displayDistribution(
        "level-distribution-eda",
        distribution.Eda ||
        {},
        "Lv"
    );


    displayDistribution(
        "level-distribution-virba",
        distribution.Virba ||
        {},
        "Lv"
    );

}


/* =========================================================
   Server Distribution
========================================================= */

function displayServerDistribution(
    distribution
) {

    displayDistribution(
        "server-distribution-eda",
        distribution.Eda ||
        {},
        ""
    );


    displayDistribution(
        "server-distribution-virba",
        distribution.Virba ||
        {},
        ""
    );

}


/* =========================================================
   Generic Distribution
========================================================= */

function displayDistribution(
    elementId,
    data,
    prefix
) {

    const container =
        document.getElementById(
            elementId
        );


    if (!container) {
        return;
    }


    const entries =
        Object.entries(
            data ||
            {}
        )
        .map(
            ([label, count]) => [
                label,
                toNumber(count)
            ]
        )
        .filter(
            ([, count]) =>
                count > 0
        );


    entries.sort(
        (a, b) => {

            const countDiff =
                b[1] -
                a[1];


            if (
                countDiff !==
                0
            ) {

                return countDiff;

            }


return String(a[0]).localeCompare(
    String(b[0]),
    "ja"
);

        }
    );


    if (!entries.length) {

        container.innerHTML =
            emptyMessage(
                "データがありません"
            );


        return;

    }


    const maxCount =
        Math.max(
            ...entries.map(
                ([, count]) =>
                    count
            )
        );


    container.innerHTML =
        entries
            .map(
                ([label, count]) => {

                    const width =
                        maxCount > 0
                            ? (
                                count /
                                maxCount *
                                100
                            )
                            : 0;


                    return `

                        <div class="distribution-row">

                            <div class="distribution-label">
                                ${escapeHtml(
                                    prefix +
                                    label
                                )}
                            </div>


                            <div class="distribution-bar-container">

                                <div
                                    class="distribution-bar"
                                    style="width:${width}%"
                                ></div>

                            </div>


                            <div class="distribution-count">
                                ${count}人
                            </div>

                        </div>

                    `;

                }
            )
            .join("");

}


/* =========================================================
   Guild Distribution
========================================================= */

function displayGuildDistribution(
    distribution
) {

    const container =
        document.getElementById(
            "guild-distribution"
        );


    if (!container) {
        return;
    }


    const entries =
        Object.entries(
            distribution ||
            {}
        )
        .map(
            ([guild, count]) => ({
                guild,
                count:
                    toNumber(
                        count
                    )
            })
        )
        .filter(
            item =>
                item.count > 0
        )
        .sort(
            (a, b) =>
                b.count -
                a.count
        )
        .slice(
            0,
            20
        );


    if (!entries.length) {

        container.innerHTML =
            emptyMessage(
                "ギルドデータがありません"
            );


        return;

    }


    const maxCount =
        Math.max(
            ...entries.map(
                item =>
                    item.count
            )
        );


    container.innerHTML =
        entries
            .map(
                (item, index) => {

                    const width =
                        maxCount > 0
                            ? (
                                item.count /
                                maxCount *
                                100
                            )
                            : 0;


                    return `

                        <div class="guild-row">

                            <div class="guild-rank">
                                ${index + 1}
                            </div>


                            <div class="guild-name">
                                ${escapeHtml(
                                    item.guild
                                )}
                            </div>


                            <div class="guild-bar-container">

                                <div
                                    class="guild-bar"
                                    style="width:${width}%"
                                ></div>

                            </div>


                            <div class="guild-count">
                                ${item.count}人
                            </div>

                        </div>

                    `;

                }
            )
            .join("");

}


/* =========================================================
   Player History
========================================================= */

async function loadPlayerHistory() {

    if (playerHistoryData) {

        return playerHistoryData;

    }


    const response =
        await fetch(
            `${PLAYER_HISTORY_URL}?t=${Date.now()}`
        );


    if (!response.ok) {

        throw new Error(
            `player_history.json の読み込みに失敗しました (${response.status})`
        );

    }


    playerHistoryData =
        await response.json();


    return playerHistoryData;

}


/* =========================================================
   Player Array
========================================================= */

function getPlayerArray() {

    if (!playerHistoryData) {

        return [];

    }


    if (
        Array.isArray(
            playerHistoryData
        )
    ) {

        return playerHistoryData;

    }


    if (
        Array.isArray(
            playerHistoryData.players
        )
    ) {

        return playerHistoryData.players;

    }


    return Object.values(
        playerHistoryData
    )
    .filter(
        item =>
            item &&
            typeof item ===
            "object" &&
            item.character
    );

}


/* =========================================================
   Player Search
========================================================= */

function setupPlayerSearch() {

    const input =
        document.getElementById(
            "player-search-input"
        );


    const button =
        document.getElementById(
            "player-search-button"
        );


    if (
        !input ||
        !button
    ) {

        return;

    }


    button.addEventListener(
        "click",
        () => {

            searchPlayers(
                input.value
            );

        }
    );


    input.addEventListener(
        "keydown",
        event => {

            if (
                event.key ===
                "Enter"
            ) {

                searchPlayers(
                    input.value
                );

            }

        }
    );


    input.addEventListener(
        "input",
        () => {

            const value =
                input.value.trim();


            const results =
                document.getElementById(
                    "player-search-results"
                );


            if (!value) {

                if (results) {

                    results.innerHTML =
                        "";

                }


                return;

            }


            searchPlayers(
                value
            );

        }
    );

}


/* =========================================================
   Search Players
========================================================= */

async function searchPlayers(
    keyword
) {

    const results =
        document.getElementById(
            "player-search-results"
        );


    if (!results) {
        return;
    }


    keyword =
        String(
            keyword ||
            ""
        ).trim();


    if (!keyword) {

        results.innerHTML =
            "";


        return;

    }


    results.innerHTML =
        `
            <div class="loading">
                検索中...
            </div>
        `;


    try {

        await loadPlayerHistory();


        const players =
            getPlayerArray();


        const normalizedKeyword =
            keyword.toLowerCase();


        const matched =
            players
                .filter(
                    player => {

                        const character =
                            String(
                                player.character ||
                                ""
                            );


                        return character
                            .toLowerCase()
                            .includes(
                                normalizedKeyword
                            );

                    }
                )
                .slice(
                    0,
                    20
                );


        if (!matched.length) {

            results.innerHTML =
                `
                    <div class="player-search-no-result">

                        「${escapeHtml(
                            keyword
                        )}」に一致する
                        プレイヤーが見つかりませんでした。

                    </div>
                `;


            return;

        }


        results.innerHTML =
            matched
                .map(
                    player =>
                        createPlayerSearchResult(
                            player
                        )
                )
                .join("");


        setupPlayerClickableElements();


    } catch (error) {

        console.error(
            error
        );


        results.innerHTML =
            `
                <div class="player-search-no-result">
                    プレイヤーデータの読み込みに失敗しました。
                </div>
            `;

    }

}


/* =========================================================
   Search Result
========================================================= */

function createPlayerSearchResult(
    player
) {

    const character =
        String(
            player.character ||
            "不明"
        );


    const current =
        player.current ||
        {};


    const status =
        player.status ||
        {};


    const lastKnown =
        player.last_known ||
        {};


    const currentLevel =
        current.level ??
        "-";


    const currentServer =
        current.server ||
        "-";


    const active =
        status.active ===
        true;


    const lastSeen =
        status.last_seen ||
        lastKnown.date ||
        "-";


    const trackingId =
        player.tracking_id ||
        "";


    return `

        <div
            class="player-search-result player-clickable"
            data-character="${escapeHtml(
                character
            )}"
            data-tracking-id="${escapeHtml(
                String(
                    trackingId
                )
            )}"
        >

            <div>

                <div class="player-search-result-name">
                    ${escapeHtml(
                        character
                    )}
                </div>


                <div class="player-search-result-info">

                    ${
                        currentLevel !==
                        "-"
                            ? `Lv${escapeHtml(
                                String(
                                    currentLevel
                                )
                            )}`
                            : "Lv-"
                    }

                    ／

                    ${escapeHtml(
                        currentServer
                    )}

                    ／

                    最終確認：

                    ${formatPlayerDate(
                        lastSeen
                    )}

                </div>

            </div>


            <div class="player-search-result-info">

                ${
                    active
                        ? "現在TOP100"
                        : "現在圏外"
                }

            </div>

        </div>

    `;

}


/* =========================================================
   Player Clickable
========================================================= */

function setupPlayerClickableElements() {

    const elements =
        document.querySelectorAll(
            ".player-clickable"
        );


    elements.forEach(
        element => {

            if (
                element.dataset.playerBound ===
                "true"
            ) {

                return;

            }


            element.dataset.playerBound =
                "true";


            element.addEventListener(
                "click",
                async event => {

                    event.stopPropagation();


                    const trackingId =
                        element.dataset.trackingId ||
                        "";


                    const character =
                        element.dataset.character ||
                        "";


                    try {

                        await loadPlayerHistory();


                        let player =
                            null;


                        if (
                            trackingId
                        ) {

                            player =
                                findPlayerByTrackingId(
                                    trackingId
                                );

                        }


                        if (
                            !player &&
                            character
                        ) {

                            player =
                                findPlayerByCharacter(
                                    character
                                );

                        }


                        if (player) {

                            openPlayerDetail(
                                player
                            );

                        }

                    } catch (error) {

                        console.error(
                            error
                        );


                        alert(
                            "プレイヤー情報の読み込みに失敗しました。"
                        );

                    }

                }
            );

        }
    );

}


/* =========================================================
   Find Player
========================================================= */

function findPlayerByTrackingId(
    trackingId
) {

    const players =
        getPlayerArray();


    return players.find(
        player =>
            String(
                player.tracking_id ||
                ""
            ) ===
            String(
                trackingId
            )
    );

}


function findPlayerByCharacter(
    character
) {

    const players =
        getPlayerArray();


    return players.find(
        player =>
            String(
                player.character ||
                ""
            ) ===
            String(
                character
            )
    );

}


/* =========================================================
   Player Modal
========================================================= */

function setupPlayerModal() {

    const closeButton =
        document.getElementById(
            "player-modal-close"
        );


    const overlay =
        document.getElementById(
            "player-modal-overlay"
        );


    if (closeButton) {

        closeButton.addEventListener(
            "click",
            closePlayerDetail
        );

    }


    if (overlay) {

        overlay.addEventListener(
            "click",
            closePlayerDetail
        );

    }


    document.addEventListener(
        "keydown",
        event => {

            if (
                event.key ===
                "Escape"
            ) {

                closePlayerDetail();

            }

        }
    );

}


/* =========================================================
   Open Player Detail
========================================================= */

function openPlayerDetail(
    player
) {

    const modal =
        document.getElementById(
            "player-modal"
        );


    const detail =
        document.getElementById(
            "player-detail"
        );


    if (
        !modal ||
        !detail
    ) {

        return;

    }


    detail.innerHTML =
        createPlayerDetailHtml(
            player
        );


    modal.classList.add(
        "is-open"
    );


    modal.setAttribute(
        "aria-hidden",
        "false"
    );


    document.body.style.overflow =
        "hidden";

}


/* =========================================================
   Close Player Detail
========================================================= */

function closePlayerDetail() {

    const modal =
        document.getElementById(
            "player-modal"
        );


    if (!modal) {
        return;
    }


    modal.classList.remove(
        "is-open"
    );


    modal.setAttribute(
        "aria-hidden",
        "true"
    );


    document.body.style.overflow =
        "";

}


/* =========================================================
   Player Detail
========================================================= */

function createPlayerDetailHtml(
    player
) {

    const character =
        String(
            player.character ||
            "不明"
        );


    const current =
        player.current ||
        {};


    const lastKnown =
        player.last_known ||
        {};


    const status =
        player.status ||
        {};


    const active =
        status.active ===
        true;


    const lastSeen =
        status.last_seen ||
        lastKnown.date ||
        "-";


    const eda =
        current.eda ||
        {};


    const virba =
        current.virba ||
        {};


    const edaVisible =
        eda.visible ===
        true;


    const virbaVisible =
        virba.visible ===
        true;


    const currentLevel =
        current.level != null
            ? current.level
            : null;


    const currentServer =
        current.server ||
        "";


    const currentGuild =
        current.guild ||
        "";


    return `

        <div class="player-detail">

            <div class="player-detail-header">

                <h2 class="player-detail-name">
                    ${escapeHtml(
                        character
                    )}
                </h2>


                <div class="player-detail-sub">

                    ${
                        active
                            ? `
                                <span class="player-current-badge">
                                    現在TOP100
                                </span>
                              `
                            : `
                                <span class="player-inactive-badge">
                                    現在圏外
                                </span>
                              `
                    }

                </div>

            </div>


            <div class="player-detail-cards">

                <div class="player-detail-card">

                    <div class="player-detail-card-label">
                        現在Lv
                    </div>


                    <div class="player-detail-card-value">

                        ${
                            currentLevel != null
                                ? `Lv${escapeHtml(
                                    String(
                                        currentLevel
                                    )
                                )}`
                                : "-"
                        }

                    </div>

                </div>


                <div class="player-detail-card">

                    <div class="player-detail-card-label">
                        現在順位
                    </div>


                    <div class="player-detail-card-value">

                        ${
                            edaVisible ||
                            virbaVisible
                                ? createCurrentRanksHtml(
                                    eda,
                                    virba
                                )
                                : "圏外"
                        }

                    </div>

                </div>


                <div class="player-detail-card">

                    <div class="player-detail-card-label">
                        サーバー
                    </div>


                    <div class="player-detail-card-value">

                        ${
                            currentServer
                                ? escapeHtml(
                                    currentServer
                                )
                                : "-"
                        }

                    </div>

                </div>


                <div class="player-detail-card">

                    <div class="player-detail-card-label">
                        ギルド
                    </div>


                    <div class="player-detail-card-value">

                        ${
                            currentGuild
                                ? escapeHtml(
                                    currentGuild
                                )
                                : "無所属"
                        }

                    </div>

                </div>

            </div>


            <div class="player-current-groups">

                ${
                    edaVisible
                        ? createCurrentGroupCard(
                            "Eda",
                            eda
                        )
                        : ""
                }


                ${
                    virbaVisible
                        ? createCurrentGroupCard(
                            "Virba",
                            virba
                        )
                        : ""
                }

            </div>


            <div class="player-detail-section">

                <h3>📌 最終確認</h3>


                <table class="player-history-table">

                    <tbody>

                        <tr>

                            <th>
                                最終確認日
                            </th>

                            <td>
                                ${formatPlayerDate(
                                    lastSeen
                                )}
                            </td>

                        </tr>


                        <tr>

                            <th>
                                最後のLv
                            </th>

                            <td>

                                ${
                                    lastKnown.level != null
                                        ? `Lv${escapeHtml(
                                            String(
                                                lastKnown.level
                                            )
                                        )}`
                                        : "-"
                                }

                            </td>

                        </tr>


                        <tr>

                            <th>
                                最後のサーバー
                            </th>

                            <td>
                                ${escapeHtml(
                                    lastKnown.server ||
                                    "-"
                                )}
                            </td>

                        </tr>


                        <tr>

                            <th>
                                最後のギルド
                            </th>

                            <td>
                                ${escapeHtml(
                                    lastKnown.guild ||
                                    "-"
                                )}
                            </td>

                        </tr>

                    </tbody>

                </table>

            </div>


            ${createRankHistoryHtml(
                player
            )}


            ${createLevelHistoryHtml(
                player
            )}


            ${createServerHistoryHtml(
                player
            )}


            ${createGuildHistoryHtml(
                player
            )}


            ${createPlayerEventsHtml(
                player
            )}

        </div>

    `;

}


/* =========================================================
   Current Ranks
========================================================= */

function createCurrentRanksHtml(
    eda,
    virba
) {

    const values = [];


    if (
        eda &&
        eda.visible &&
        eda.rank != null
    ) {

        values.push(
            `Eda ${escapeHtml(
                String(
                    eda.rank
                )
            )}位`
        );

    }


    if (
        virba &&
        virba.visible &&
        virba.rank != null
    ) {

        values.push(
            `Virba ${escapeHtml(
                String(
                    virba.rank
                )
            )}位`
        );

    }


    if (!values.length) {

        return "圏外";

    }


    return values.join(
        "<br>"
    );

}


/* =========================================================
   Current Group Card
========================================================= */

function createCurrentGroupCard(
    group,
    data
) {

    return `

        <div class="player-current-group-card">

            <div class="player-current-group-name">
                ${escapeHtml(
                    group
                )}
            </div>


            <div class="player-current-group-info">

                <span>

                    ${
                        data.rank != null
                            ? `${escapeHtml(
                                String(
                                    data.rank
                                )
                            )}位`
                            : "-"
                    }

                </span>


                <span>

                    ${
                        data.level != null
                            ? `Lv${escapeHtml(
                                String(
                                    data.level
                                )
                            )}`
                            : "-"
                    }

                </span>


                <span>
                    ${escapeHtml(
                        data.server ||
                        "-"
                    )}
                </span>


                <span>
                    ${escapeHtml(
                        data.guild ||
                        "無所属"
                    )}
                </span>

            </div>

        </div>

    `;

}


/* =========================================================
   History Records
========================================================= */

function getPlayerHistoryRecords(
    player
) {

    if (
        !Array.isArray(
            player.history
        )
    ) {

        return [];

    }


    return [
        ...player.history
    ]
    .sort(
        (a, b) =>
            String(
                a.date
            ).localeCompare(
                String(
                    b.date
                )
            )
    );

}


/* =========================================================
   Rank History
========================================================= */

function createRankHistoryHtml(
    player
) {

    const history =
        getPlayerHistoryRecords(
            player
        );


    if (!history.length) {
        return "";
    }


    const rows =
        history
            .map(
                record => {

                    const eda =
                        record.server_ranking?.Eda;


                    const virba =
                        record.server_ranking?.Virba;


                    return `

                        <tr>

                            <td>
                                ${formatPlayerDate(
                                    record.date
                                )}
                            </td>


                            <td>

                                ${
                                    eda?.visible &&
                                    eda.rank != null
                                        ? `Eda ${escapeHtml(
                                            String(
                                                eda.rank
                                            )
                                        )}位`
                                        : "-"
                                }

                            </td>


                            <td>

                                ${
                                    virba?.visible &&
                                    virba.rank != null
                                        ? `Virba ${escapeHtml(
                                            String(
                                                virba.rank
                                            )
                                        )}位`
                                        : "-"
                                }

                            </td>

                        </tr>

                    `;

                }
            )
            .join("");


    return `

        <div class="player-detail-section">

            <h3>📈 順位推移</h3>


            <div class="player-history-scroll">

                <table class="player-history-table">

                    <thead>

                        <tr>

                            <th>日付</th>

                            <th>Eda</th>

                            <th>Virba</th>

                        </tr>

                    </thead>


                    <tbody>
                        ${rows}
                    </tbody>

                </table>

            </div>

        </div>

    `;

}


/* =========================================================
   Level History
========================================================= */

function createLevelHistoryHtml(
    player
) {

    const history =
        getPlayerHistoryRecords(
            player
        );


    const rows =
        history
            .map(
                record => {

                    const eda =
                        record.server_ranking?.Eda;


                    const virba =
                        record.server_ranking?.Virba;


                    const edaValue =
                        eda?.visible &&
                        eda.level != null
                            ? `Lv${escapeHtml(
                                String(
                                    eda.level
                                )
                            )}`
                            : "-";


                    const virbaValue =
                        virba?.visible &&
                        virba.level != null
                            ? `Lv${escapeHtml(
                                String(
                                    virba.level
                                )
                            )}`
                            : "-";


                    if (
                        edaValue === "-" &&
                        virbaValue === "-"
                    ) {

                        return "";

                    }


                    return `

                        <tr>

                            <td>
                                ${formatPlayerDate(
                                    record.date
                                )}
                            </td>


                            <td>
                                ${edaValue}
                            </td>


                            <td>
                                ${virbaValue}
                            </td>

                        </tr>

                    `;

                }
            )
            .filter(Boolean)
            .join("");


    if (!rows) {
        return "";
    }


    return `

        <div class="player-detail-section">

            <h3>📊 レベル推移</h3>


            <div class="player-history-scroll">

                <table class="player-history-table">

                    <thead>

                        <tr>

                            <th>日付</th>

                            <th>Eda</th>

                            <th>Virba</th>

                        </tr>

                    </thead>


                    <tbody>
                        ${rows}
                    </tbody>

                </table>

            </div>

        </div>

    `;

}


/* =========================================================
   Server History
========================================================= */

function createServerHistoryHtml(
    player
) {

    const history =
        getPlayerHistoryRecords(
            player
        );


    const rows =
        history
            .map(
                record => {

                    const eda =
                        record.server_ranking?.Eda;


                    const virba =
                        record.server_ranking?.Virba;


                    const edaValue =
                        eda?.visible &&
                        eda.server
                            ? escapeHtml(
                                eda.server
                            )
                            : "-";


                    const virbaValue =
                        virba?.visible &&
                        virba.server
                            ? escapeHtml(
                                virba.server
                            )
                            : "-";


                    if (
                        edaValue === "-" &&
                        virbaValue === "-"
                    ) {

                        return "";

                    }


                    return `

                        <tr>

                            <td>
                                ${formatPlayerDate(
                                    record.date
                                )}
                            </td>


                            <td>
                                ${edaValue}
                            </td>


                            <td>
                                ${virbaValue}
                            </td>

                        </tr>

                    `;

                }
            )
            .filter(Boolean)
            .join("");


    if (!rows) {
        return "";
    }


    return `

        <div class="player-detail-section">

            <h3>🖥 サーバー推移</h3>


            <div class="player-history-scroll">

                <table class="player-history-table">

                    <thead>

                        <tr>

                            <th>日付</th>

                            <th>Eda</th>

                            <th>Virba</th>

                        </tr>

                    </thead>


                    <tbody>
                        ${rows}
                    </tbody>

                </table>

            </div>

        </div>

    `;

}


/* =========================================================
   Guild History
========================================================= */

function createGuildHistoryHtml(
    player
) {

    const history =
        getPlayerHistoryRecords(
            player
        );


    const rows =
        history
            .map(
                record => {

                    const eda =
                        record.server_ranking?.Eda;


                    const virba =
                        record.server_ranking?.Virba;


                    const edaValue =
                        eda?.visible &&
                        eda.guild
                            ? escapeHtml(
                                eda.guild
                            )
                            : "-";


                    const virbaValue =
                        virba?.visible &&
                        virba.guild
                            ? escapeHtml(
                                virba.guild
                            )
                            : "-";


                    if (
                        edaValue === "-" &&
                        virbaValue === "-"
                    ) {

                        return "";

                    }


                    return `

                        <tr>

                            <td>
                                ${formatPlayerDate(
                                    record.date
                                )}
                            </td>


                            <td>
                                ${edaValue}
                            </td>


                            <td>
                                ${virbaValue}
                            </td>

                        </tr>

                    `;

                }
            )
            .filter(Boolean)
            .join("");


    if (!rows) {
        return "";
    }


    return `

        <div class="player-detail-section">

            <h3>⚔️ ギルド推移</h3>


            <div class="player-history-scroll">

                <table class="player-history-table">

                    <thead>

                        <tr>

                            <th>日付</th>

                            <th>Eda</th>

                            <th>Virba</th>

                        </tr>

                    </thead>


                    <tbody>
                        ${rows}
                    </tbody>

                </table>

            </div>

        </div>

    `;

}


/* =========================================================
   Player Events
========================================================= */

function createPlayerEventsHtml(
    player
) {

    if (
        !Array.isArray(
            player.events
        )
    ) {

        return "";

    }


    if (
        !player.events.length
    ) {

        return "";

    }


    const events =
        [
            ...player.events
        ]
        .sort(
            (a, b) =>
                String(
                    b.date
                ).localeCompare(
                    String(
                        a.date
                    )
                )
        );


    const rows =
        events
            .map(
                event => {

                    const label =
                        getPlayerEventLabel(
                            event.type
                        );


                    const oldValue =
                        event.old_value;


                    const newValue =
                        event.new_value;


                    let value =
                        "";


                    if (
                        oldValue != null &&
                        newValue != null
                    ) {

                        value =
                            `${formatPlayerValue(
                                oldValue
                            )} → ${formatPlayerValue(
                                newValue
                            )}`;

                    } else if (
                        newValue != null
                    ) {

                        value =
                            formatPlayerValue(
                                newValue
                            );

                    } else if (
                        oldValue != null
                    ) {

                        value =
                            formatPlayerValue(
                                oldValue
                            );

                    }


                    if (event.group) {

                        value =
                            `
                                <span class="event-group-label">
                                    ${escapeHtml(
                                        String(
                                            event.group
                                        )
                                    )}
                                </span>
                                ${value}
                            `;

                    }


                    const flags = [];


                    if (
                        event.first_observation ===
                        true
                    ) {

                        flags.push(
                            "初観測"
                        );

                    }


                    if (
                        event.gap ===
                        true
                    ) {

                        flags.push(
                            "期間空白後"
                        );

                    }


                    return `

                        <div class="player-event">

                            <div class="player-event-date">
                                ${formatPlayerDate(
                                    event.date
                                )}
                            </div>


                            <div class="player-event-label">

                                ${escapeHtml(
                                    label
                                )}

                                ${
                                    flags.length
                                        ? `
                                            <span class="player-event-flag">
                                                ${escapeHtml(
                                                    flags.join(
                                                        " / "
                                                    )
                                                )}
                                            </span>
                                          `
                                        : ""
                                }

                            </div>


                            <div class="player-event-value">
                                ${value}
                            </div>

                        </div>

                    `;

                }
            )
            .join("");


    return `

        <div class="player-detail-section">

            <h3>📋 イベント履歴</h3>


            <div class="player-event-list">

                ${rows}

            </div>

        </div>

    `;

}


/* =========================================================
   Event Labels
========================================================= */

function getPlayerEventLabel(
    type
) {

    const labels = {

        server_ranking_entry:
            "TOP100入り",

        server_ranking_exit:
            "TOP100圏外",

        server_rank_up:
            "順位上昇",

        server_rank_down:
            "順位下降",

        server_ranking_level_up:
            "レベルアップ",

        server_ranking_level_down:
            "レベルダウン",

        server_ranking_guild_change:
            "ギルド変更",

        server_ranking_server_change:
            "サーバー変更"

    };


    return (
        labels[type] ||
        type ||
        "イベント"
    );

}


/* =========================================================
   Event Value
========================================================= */

function formatPlayerValue(
    value
) {

    if (
        value == null
    ) {

        return "";

    }


    if (
        typeof value ===
        "object"
    ) {

        if (
            value.rank != null
        ) {

            return escapeHtml(
                String(
                    value.rank
                )
            );

        }


        if (
            value.level != null
        ) {

            return escapeHtml(
                String(
                    value.level
                )
            );

        }


        if (
            value.guild != null
        ) {

            return escapeHtml(
                String(
                    value.guild
                )
            );

        }


        if (
            value.server != null
        ) {

            return escapeHtml(
                String(
                    value.server
                )
            );

        }


        return escapeHtml(
            JSON.stringify(
                value
            )
        );

    }


    return escapeHtml(
        String(
            value
        )
    );

}


/* =========================================================
   Date
========================================================= */

function formatPlayerDate(
    date
) {

    const value =
        String(
            date ||
            ""
        );


    if (
        !/^\d{8}$/.test(
            value
        )
    ) {

        return escapeHtml(
            value
        );

    }


    return (
        value.substring(
            0,
            4
        ) +
        "/" +
        value.substring(
            4,
            6
        ) +
        "/" +
        value.substring(
            6,
            8
        )
    );

}


/* =========================================================
   Helpers
========================================================= */

function setText(
    id,
    value
) {

    const element =
        document.getElementById(
            id
        );


    if (element) {

        element.textContent =
            value;

    }

}


function toNumber(
    value
) {

    const number =
        Number(
            value
        );


    return Number.isFinite(
        number
    )
        ? number
        : 0;

}


function numberFormat(
    value
) {

    return toNumber(
        value
    ).toLocaleString(
        "ja-JP"
    );

}


function formatDate(
    date
) {

    if (!date) {
        return "-";
    }


    const value =
        String(
            date
        );


    if (
        /^\d{8}$/.test(
            value
        )
    ) {

        return (
            value.substring(
                0,
                4
            ) +
            "/" +
            value.substring(
                4,
                6
            ) +
            "/" +
            value.substring(
                6,
                8
            )
        );

    }


    return value;

}


/* =========================================================
   Escape HTML
========================================================= */

function escapeHtml(
    text
) {

    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        text ??
        "";


    return div.innerHTML;

}


/* =========================================================
   Empty Message
========================================================= */

function emptyMessage(
    message
) {

    return `

        <div class="loading">

            ${escapeHtml(
                message
            )}

        </div>

    `;

}


/* =========================================================
   Error
========================================================= */

function showError(
    message
) {

    const existing =
        document.getElementById(
            "app-error"
        );


    if (existing) {

        existing.remove();

    }


    const div =
        document.createElement(
            "div"
        );


    div.id =
        "app-error";


    div.style.cssText = `

        margin:20px auto;

        padding:20px;

        max-width:1200px;

        color:#991b1b;

        background:#fef2f2;

        border:1px solid #fecaca;

        border-radius:12px;

    `;


    div.innerHTML = `

        <strong>
            データの読み込みに失敗しました。
        </strong>

        <br><br>

        ${escapeHtml(
            message
        )}

    `;


    document.body.prepend(
        div
    );

}

/* =========================================================
   Server Distribution Guild Members Modal
========================================================= */

function setupDashboardGuildButtons() {
    const buttons =
        document.querySelectorAll(
            ".dashboard-server-guild"
        );

    buttons.forEach(button => {
        button.addEventListener(
            "click",
            () => {
                const server =
                    button.dataset.server || "";

                const guild =
                    button.dataset.guild || "";

                openGuildMembersModal(
                    server,
                    guild
                );
            }
        );
    });
}

function setupDashboardLevelButtons() {

    const buttons =
        document.querySelectorAll(
            ".dashboard-level-button"
        );


    buttons.forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const level =
                    Number(
                        button.dataset.level
                    );


                if (!Number.isFinite(level)) {
                    return;
                }


                openLevelMembersModal(
                    level
                );

            }
        );

    });

}

function setupDashboardHighlightButtons() {

    const cards =
        document.querySelectorAll(
            ".dashboard-highlight-card"
        );

    if (!cards.length) {
        return;
    }

    cards.forEach((card, index) => {

        card.style.cursor = "pointer";

        card.addEventListener(
            "click",
            () => {

                if (!currentData) {
                    return;
                }

                const types = [
                    "level_up",
                    "rank_up",
                    "rank_down"
                ];

                openDashboardHighlightModal(
                    types[index]
                );

            }
        );

    });

}

/* =========================================================
   Dashboard Highlight Modal
   共通キャラ一覧モーダルを使用
========================================================= */

function openDashboardHighlightModal(
    type
) {

    if (
        !currentData ||
        !currentData.rankings
    ) {
        return;
    }


    const events =
        filterTodayEvents(
            currentData.rankings[type] || []
        );


    const titles = {

        level_up:
            "🆙 本日のLv UP",

        rank_up:
            "📈 順位上昇",

        rank_down:
            "📉 順位下降"

    };


    const title =
        titles[type] ||
        "今日の注目";


    const players =
        getUniqueCombinedRanking(
            currentData
        );


    const members =
        events
            .map(
                event => {

                    const character =
                        String(
                            event.character ||
                            ""
                        );


                    const currentPlayer =
                        players.find(
                            player =>
                                String(
                                    player.character ||
                                    ""
                                ) === character
                        );


                    if (!currentPlayer) {
                        return null;
                    }


                    return {

                        rank:
                            currentPlayer.rank,

                        server:
                            currentPlayer.server,

                        character:
                            currentPlayer.character,

                        guild:
                            currentPlayer.guild

                    };

                }
            )
            .filter(
                player =>
                    player !== null
            )
            .sort(
                (a, b) => {

                    const rankA =
                        Number(a.rank);

                    const rankB =
                        Number(b.rank);


                    if (
                        Number.isFinite(rankA) &&
                        Number.isFinite(rankB)
                    ) {
                        return rankA - rankB;
                    }


                    return String(
                        a.character || ""
                    ).localeCompare(
                        String(
                            b.character || ""
                        ),
                        "ja"
                    );

                }
            );


    openCharacterListModal(
        title,
        `${members.length}人`,
        members
    );

}
/* =========================================================
   Dashboard Guild Members Modal
   共通キャラ一覧モーダルを使用
========================================================= */

function openGuildMembersModal(
    server,
    guild
) {

    if (
        !dashboardServerDistributionData
    ) {
        return;
    }


    const players =
        getUniqueCombinedRanking(
            dashboardServerDistributionData
        );


    const members =
        players
            .filter(
                player =>
                    String(
                        player.server || ""
                    ) === String(server) &&
                    String(
                        player.guild || ""
                    ).trim() === String(guild).trim()
            )
            .sort(
                (a, b) => {

                    const rankA =
                        Number(a.rank);

                    const rankB =
                        Number(b.rank);


                    if (
                        Number.isFinite(rankA) &&
                        Number.isFinite(rankB)
                    ) {
                        return rankA - rankB;
                    }


                    return String(
                        a.character || ""
                    ).localeCompare(
                        String(
                            b.character || ""
                        ),
                        "ja"
                    );

                }
            );


    openCharacterListModal(
        `🏰 ${guild}`,
        `${server} / ${members.length}人`,
        members
    );

}

/* =========================================================
   共通キャラクター一覧モーダル
========================================================= */

function openCharacterListModal(
    title,
    subtitle,
    rows
) {

    const existing =
        document.getElementById(
            "character-list-modal"
        );

    if (existing) {
        existing.remove();
    }


    const modal =
        document.createElement(
            "div"
        );

    modal.id =
        "character-list-modal";

    modal.className =
        "guild-members-modal";


    const rowHtml =
        rows.length
            ? rows.join("")
            : `
                <tr>
                    <td
                        colspan="5"
                        class="guild-members-empty"
                    >
                        該当するキャラクターはいません
                    </td>
                </tr>
            `;


    modal.innerHTML = `
        <div
            class="guild-members-modal-backdrop"
        ></div>

        <div
            class="guild-members-modal-dialog"
            role="dialog"
            aria-modal="true"
        >

            <div
                class="guild-members-modal-header"
            >

                <div>

                    <div
                        class="guild-members-modal-title"
                    >
                        ${escapeHtml(title)}
                    </div>

                    <div
                        class="guild-members-modal-subtitle"
                    >
                        ${escapeHtml(subtitle)}
                    </div>

                </div>

                <button
                    type="button"
                    class="guild-members-modal-close"
                    aria-label="閉じる"
                >
                    ×
                </button>

            </div>


            <div
                class="guild-members-modal-body"
            >

                <table
                    class="guild-members-table"
                >

                    <thead>
                        <tr>
                            <th>順位</th>
                            <th>Lv</th>
                            <th>キャラクター</th>
                            <th>所属</th>
                            <th>変動</th>
                        </tr>
                    </thead>

                    <tbody>
                        ${rowHtml}
                    </tbody>

                </table>

            </div>

        </div>
    `;


    document.body.appendChild(
        modal
    );


    const closeButton =
        modal.querySelector(
            ".guild-members-modal-close"
        );

    const backdrop =
        modal.querySelector(
            ".guild-members-modal-backdrop"
        );


    const closeModal = () => {
        modal.remove();
    };


    closeButton?.addEventListener(
        "click",
        closeModal
    );

    backdrop?.addEventListener(
        "click",
        closeModal
    );


    setupPlayerClickableElements();

}


/* =========================================================
   Dashboard Level Members Modal
   共通キャラ一覧モーダルを使用
========================================================= */

function openLevelMembersModal(
    level
) {

    if (
        !dashboardLevelDistributionData
    ) {
        return;
    }


    const players =
        getUniqueCombinedRanking(
            dashboardLevelDistributionData
        );


    const members =
        players
            .filter(
                player =>
                    getPlayerLevel(
                        player
                    ) === level
            )
            .sort(
                (a, b) => {

                    const rankA =
                        Number(a.rank);

                    const rankB =
                        Number(b.rank);


                    if (
                        Number.isFinite(rankA) &&
                        Number.isFinite(rankB)
                    ) {
                        return rankA - rankB;
                    }


                    return String(
                        a.character || ""
                    ).localeCompare(
                        String(
                            b.character || ""
                        ),
                        "ja"
                    );

                }
            );


    openCharacterListModal(
        `⭐ Lv${level}`,
        `${members.length}人`,
        members
    );

}

/* =========================================================
   Character List Common Modal
   レベル分布モーダルをベースにした共通キャラ一覧
========================================================= */

function openCharacterListModal(
    title,
    subtitle,
    members
) {

    const existing =
        document.getElementById(
            "character-list-modal"
        );

    if (existing) {
        existing.remove();
    }


    const modal =
        document.createElement("div");

    modal.id =
        "character-list-modal";

    modal.className =
        "guild-members-modal";


    const memberRows =
        members.length
            ? members
                .map(
                    player => {

                        const rank =
                            Number(
                                player.rank
                            );

                        const server =
                            String(
                                player.server ||
                                ""
                            );

                        const guild =
                            String(
                                player.guild ||
                                ""
                            ).trim();

                        const character =
                            String(
                                player.character ||
                                ""
                            );


                        return `
                            <div
                                class="guild-member-row player-clickable"
                                data-character="${escapeHtml(
                                    character
                                )}"
                            >

                                <div class="guild-member-rank">
                                    ${
                                        Number.isFinite(
                                            rank
                                        )
                                            ? `${rank}位`
                                            : "-"
                                    }
                                </div>


                                <div class="guild-member-level">
                                    ${escapeHtml(
                                        server
                                    )}
                                </div>


                                <div class="guild-member-character">

                                    ${escapeHtml(
                                        character
                                    )}

                                    ${
                                        guild
                                            ? `
                                                <span
                                                    style="
                                                        margin-left:8px;
                                                        font-size:0.85em;
                                                        color:#6b7280;
                                                    "
                                                >
                                                    ${escapeHtml(
                                                        guild
                                                    )}
                                                </span>
                                            `
                                            : ""
                                    }

                                </div>

                            </div>
                        `;

                    }
                )
                .join("")
            : `
                <div class="guild-members-empty">
                    キャラクターが見つかりません
                </div>
            `;


    modal.innerHTML = `
        <div class="guild-members-modal-backdrop"></div>


        <div
            class="guild-members-modal-dialog"
            role="dialog"
            aria-modal="true"
        >

            <div class="guild-members-modal-header">

                <div>

                    <div class="guild-members-modal-title">
                        ${escapeHtml(title)}
                    </div>


                    <div class="guild-members-modal-subtitle">
                        ${escapeHtml(subtitle)}
                    </div>

                </div>


                <button
                    type="button"
                    class="guild-members-modal-close"
                    aria-label="閉じる"
                >
                    ×
                </button>

            </div>


            <div class="guild-members-table-header">

                <div>順位</div>

                <div>サーバー</div>

                <div>キャラクター / ギルド</div>

            </div>


            <div class="guild-members-list">
                ${memberRows}
            </div>

        </div>
    `;


    document.body.appendChild(
        modal
    );


    const closeModal =
        () => {
            modal.remove();
        };


    modal
        .querySelector(
            ".guild-members-modal-close"
        )
        .addEventListener(
            "click",
            closeModal
        );


    modal
        .querySelector(
            ".guild-members-modal-backdrop"
        )
        .addEventListener(
            "click",
            closeModal
        );


    document.addEventListener(
        "keydown",
        function handleEscape(event) {

            if (
                event.key === "Escape"
            ) {

                closeModal();

                document.removeEventListener(
                    "keydown",
                    handleEscape
                );

            }

        }
    );


    setupPlayerClickableElements();

}

function setupSearchTypeTabs() {

    const tabs =
        document.querySelectorAll(
            ".search-type-tab"
        );

    if (!tabs.length) {
        return;
    }

    const playerSearch =
        document.querySelector(
            ".player-search"
        );

    if (!playerSearch) {
        return;
    }

    tabs.forEach(tab => {

        tab.addEventListener(
            "click",
            () => {

                const type =
                    tab.dataset.searchType;

                tabs.forEach(
                    item => {
                        item.classList.toggle(
                            "active",
                            item === tab
                        );
                    }
                );

                if (
                    type === "guild"
                ) {

                    playerSearch.style.display =
                        "none";

                    showGuildSearch();

                } else {

                    playerSearch.style.display =
                        "";

                    const guildSearch =
                        document.getElementById(
                            "guild-search"
                        );

                    if (guildSearch) {
                        guildSearch.remove();
                    }

                }

            }
        );

    });

}

function showGuildSearch() {

    const existing =
        document.getElementById(
            "guild-search"
        );

    if (existing) {
        return;
    }

    const playerSearch =
        document.querySelector(
            ".player-search"
        );

    if (!playerSearch) {
        return;
    }

    const guildSearch =
        document.createElement("div");

    guildSearch.id =
        "guild-search";

    guildSearch.className =
        "player-search";

    guildSearch.innerHTML = `
        <div class="player-search-box">

            <input
                type="text"
                id="guild-search-input"
                placeholder="ギルド名を入力..."
                autocomplete="off"
            >

            <button
                type="button"
                id="guild-search-button"
            >
                検索
            </button>

        </div>

        <div
            id="guild-search-results"
            class="player-search-results"
        ></div>
    `;

       playerSearch.parentNode.insertBefore(
        guildSearch,
        playerSearch.nextSibling
    );

    setupGuildSearch();

    function setupGuildSearch() {

    const input =
        document.getElementById(
            "guild-search-input"
        );

    const button =
        document.getElementById(
            "guild-search-button"
        );

    if (!input || !button) {
        return;
    }

    button.addEventListener(
        "click",
        () => {
            searchGuilds(
                input.value
            );
        }
    );

    input.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Enter"
            ) {

                searchGuilds(
                    input.value
                );

            }

        }
    );

    input.addEventListener(
        "input",
        () => {

            const value =
                input.value.trim();

            if (!value) {

                const results =
                    document.getElementById(
                        "guild-search-results"
                    );

                if (results) {
                    results.innerHTML = "";
                }

                return;
            }

            searchGuilds(value);

        }
    );

}

async function searchGuilds(
    keyword
) {

    const results =
        document.getElementById(
            "guild-search-results"
        );

    if (!results) {
        return;
    }

    keyword =
        String(
            keyword || ""
        ).trim();

    if (!keyword) {
        results.innerHTML = "";
        return;
    }

    results.innerHTML = `
        <div class="loading">
            検索中...
        </div>
    `;

    try {

        await loadPlayerHistory();

        const players =
            getPlayerArray();

        const normalizedKeyword =
            keyword.toLowerCase();

        const guildMap = {};

        players.forEach(
            player => {

                const guild =
                    String(
                        player.current?.guild ??
                        ""
                    ).trim();

                if (!guild) {
                    return;
                }

                if (
                    !guild
                        .toLowerCase()
                        .includes(
                            normalizedKeyword
                        )
                ) {
                    return;
                }

                if (!guildMap[guild]) {
                    guildMap[guild] = [];
                }

                guildMap[guild].push(
                    player
                );

            }
        );

        const matchedGuilds =
            Object.entries(
                guildMap
            )
            .sort(
                (a, b) =>
                    b[1].length -
                    a[1].length ||
                    a[0].localeCompare(
                        b[0],
                        "ja"
                    )
            )
            .slice(0, 20);

        if (!matchedGuilds.length) {

            results.innerHTML = `
                <div class="player-search-no-result">
                    「${escapeHtml(
                        keyword
                    )}」に一致する
                    ギルドが見つかりませんでした。
                </div>
            `;

            return;
        }

        results.innerHTML =
            matchedGuilds
                .map(
                    ([guild, members]) => `
                        <div
                            class="player-search-result guild-search-result"
                            data-guild="${escapeHtml(
                                guild
                            )}"
                        >

                            <div>
                                <div class="player-search-result-name">
                                    🏰 ${escapeHtml(
                                        guild
                                    )}
                                </div>

                                <div class="player-search-result-info">
                                    現在所属
                                </div>
                            </div>

                            <div class="player-search-result-info">
                                ${members.length}人
                            </div>

                        </div>
                    `
                )
                .join("");

        results
            .querySelectorAll(
                ".guild-search-result"
            )
            .forEach(
                element => {

                    element.addEventListener(
                        "click",
                        () => {

                            const guild =
                                element.dataset.guild ||
                                "";

                            const members =
                                players
                                    .filter(
                                        player =>
                                            String(
                                                player.current?.guild ??
                                                ""
                                            ).trim() ===
                                            guild
                                    );

                            openCharacterListModal(
                                `🏰 ${guild}`,
                                `${members.length}人`,
                                members.map(
                                    player => ({
                                        rank:
                                            player.current?.rank,

                                        server:
                                            player.current?.server,

                                        character:
                                            player.character,

                                        guild:
                                            player.current?.guild
                                    })
                                )
                            );

                        }
                    );

                }
            );

    } catch (error) {

        console.error(
            error
        );

        results.innerHTML = `
            <div class="player-search-no-result">
                ギルドデータの読み込みに失敗しました。
            </div>
        `;

    }

}

}