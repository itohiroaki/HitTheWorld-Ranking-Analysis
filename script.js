let currentData = null;
let historyData = null;


/* ========================= */
/* 初期読み込み */
/* ========================= */

async function loadData() {

    try {

        /*
         * 最新データ
         */

        const dataResponse =
            await fetch("data.json");


        if (!dataResponse.ok) {

            throw new Error(
                "data.jsonを読み込めませんでした"
            );

        }


        let loadedData =
            await dataResponse.json();


        /*
         * data.json が配列の場合
         *
         * [
         *   {...}
         * ]
         *
         * 最新の1件を使用
         */

        if (Array.isArray(loadedData)) {

            if (loadedData.length === 0) {

                throw new Error(
                    "data.jsonが空です"
                );

            }

            /*
             * dateが新しいものを取得
             */

            loadedData.sort(
                (a, b) =>
                    String(b.date).localeCompare(
                        String(a.date)
                    )
            );


            currentData =
                loadedData[0];

        } else {

            currentData =
                loadedData;

        }


        /*
         * 履歴データ
         */

        const historyResponse =
            await fetch("history.json");


        if (!historyResponse.ok) {

            throw new Error(
                "history.jsonを読み込めませんでした"
            );

        }


        historyData =
            await historyResponse.json();


        /*
         * 履歴一覧
         */

        displayHistory();


        /*
         * 最新データ表示
         */

        displayData(
            currentData
        );


    } catch (error) {

        console.error(
            "データ読み込みエラー:",
            error
        );


        document.body.innerHTML +=
            `
            <div style="
                margin:20px;
                padding:20px;
                color:red;
                background:white;
                border:1px solid red;
                border-radius:8px;
            ">
                <strong>
                    データの読み込みに失敗しました。
                </strong>

                <br><br>

                ${escapeHtml(error.message)}
            </div>
            `;

    }

}


/* ========================= */
/* 履歴一覧 */
/* ========================= */

function displayHistory() {

    const select =
        document.getElementById(
            "history-date"
        );


    select.innerHTML = "";


    let dates = [];


    /*
     * history.jsonが配列
     */

    if (Array.isArray(historyData)) {

        dates =
            historyData
                .map(item => item.date)
                .filter(Boolean);

    }


    /*
     * history.jsonがオブジェクト
     */

    else if (
        historyData &&
        typeof historyData === "object"
    ) {

        dates =
            Object.keys(historyData);

    }


    /*
     * 重複削除
     */

    dates =
        [...new Set(dates)];


    /*
     * 新しい日付順
     */

    dates.sort(
        (a, b) =>
            String(b).localeCompare(
                String(a)
            )
    );


    /*
     * セレクトボックス作成
     */

    dates.forEach(
        date => {

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

        }
    );


    /*
     * 最新日を選択
     */

    if (
        currentData &&
        currentData.date
    ) {

        select.value =
            currentData.date;

    }


    /*
     * 日付変更イベント
     */

    select.onchange =
        () => {

            loadHistoryDate(
                select.value
            );

        };

}


/* ========================= */
/* 履歴データ読み込み */
/* ========================= */

async function loadHistoryDate(date) {

    try {

        /*
         * 最新日
         */

        if (
            currentData &&
            date === currentData.date
        ) {

            displayData(
                currentData
            );

            return;

        }


        /*
         * history.jsonが配列
         */

        if (
            Array.isArray(historyData)
        ) {

            const item =
                historyData.find(
                    item =>
                        item.date === date
                );


            if (item) {

                displayData(
                    item
                );

                return;

            }

        }


        /*
         * history.jsonがオブジェクト
         */

        if (
            historyData &&
            typeof historyData === "object" &&
            !Array.isArray(historyData)
        ) {

            const item =
                historyData[date];


            if (item) {

                /*
                 * 直接データ
                 */

                if (
                    typeof item === "object"
                ) {

                    displayData(
                        item
                    );

                    return;

                }


                /*
                 * ファイルパス
                 */

                if (
                    typeof item === "string"
                ) {

                    const response =
                        await fetch(item);


                    if (!response.ok) {

                        throw new Error(
                            `履歴データを読み込めませんでした：${date}`
                        );

                    }


                    const data =
                        await response.json();


                    displayData(
                        data
                    );

                    return;

                }

            }

        }


        /*
         * 個別履歴ファイル
         *
         * history/data_YYYYMMDD.json
         */

        const response =
            await fetch(
                `history/data_${date}.json`
            );


        if (response.ok) {

            const data =
                await response.json();


            displayData(
                data
            );

            return;

        }


        throw new Error(
            `履歴データが見つかりません：${date}`
        );


    } catch (error) {

        console.error(error);


        alert(
            "履歴データの読み込みに失敗しました。\n"
            + error.message
        );

    }

}


/* ========================= */
/* 選択したデータを表示 */
/* ========================= */

function displayData(data) {

    /*
     * 念のため配列にも対応
     */

    if (Array.isArray(data)) {

        if (data.length === 0) {

            throw new Error(
                "表示するデータがありません"
            );

        }

        data =
            data[0];

    }


    displayBasic(data);

    displayLevels(data);

    displayServers(data);

    displayGuilds(data);

}


/* ========================= */
/* 基本情報 */
/* ========================= */

function displayBasic(data) {

    const date =
        data.date;


    document.getElementById(
        "update-date"
    ).textContent =
        `データ更新日：${formatDate(date)}`;


    document.getElementById(
        "total"
    ).textContent =
        Number(data.total).toLocaleString();


    document.getElementById(
        "max-level"
    ).textContent =
        `Lv${data.level.max}`;


    document.getElementById(
        "average-level"
    ).textContent =
        data.level.average;


    document.getElementById(
        "min-level"
    ).textContent =
        `Lv${data.level.min}`;


    document.getElementById(
        "most-level"
    ).textContent =
        `Lv${data.level.most[0]}`;


    document.getElementById(
        "most-count"
    ).textContent =
        `${data.level.most_count}人`;

}


/* ========================= */
/* レベル */
/* ========================= */

function displayLevels(data) {

    const container =
        document.getElementById(
            "level-list"
        );


    const levels =
        data.level.distribution;


    const values =
        Object.values(levels);


    const maxCount =
        Math.max(...values);


    container.innerHTML = "";


    Object.entries(levels)
        .forEach(
            ([level, count]) => {


                const width =
                    maxCount > 0
                        ? (
                            count /
                            maxCount *
                            100
                        )
                        : 0;


                const row =
                    document.createElement(
                        "div"
                    );


                row.className =
                    "level-row";


                row.innerHTML =
                    `
                    <div>
                        Lv${level}
                    </div>

                    <div class="level-bar-container">

                        <div
                            class="level-bar"
                            style="width:${width}%"
                        ></div>

                    </div>

                    <div>
                        ${count}人
                    </div>
                    `;


                container.appendChild(
                    row
                );

            }
        );

}


/* ========================= */
/* サーバー */
/* ========================= */

function displayServers(data) {

    const container =
        document.getElementById(
            "server-list"
        );


    const servers =
        data.server.distribution;


    const values =
        Object.values(servers);


    const maxCount =
        Math.max(...values);


    container.innerHTML = "";


    /*
     * ========================================
     * サーバーごとの主要ギルドを集計
     * ========================================
     */

    const serverGuildCounts = {};


    if (Array.isArray(data.ranking)) {

        data.ranking.forEach(
            player => {

                const server =
                    String(
                        player.server ?? ""
                    ).trim();


                const guild =
                    String(
                        player.guild ?? ""
                    ).trim();


                /*
                 * サーバー・ギルドが
                 * 空の場合は除外
                 */

                if (
                    !server ||
                    !guild
                ) {
                    return;
                }


                if (
                    !serverGuildCounts[server]
                ) {

                    serverGuildCounts[server] = {};

                }


                if (
                    !serverGuildCounts[server][guild]
                ) {

                    serverGuildCounts[server][guild] = 0;

                }


                serverGuildCounts[server][guild]++;

            }
        );

    }


    /*
     * ========================================
     * サーバー一覧表示
     * ========================================
     */

    Object.entries(servers)
        .forEach(
            ([server, count]) => {


                const width =
                    maxCount > 0
                        ? (
                            count /
                            maxCount *
                            100
                        )
                        : 0;


                /*
                 * -------------------------
                 * 主要ギルドTOP3
                 * -------------------------
                 */

                let majorGuilds = [];


                if (
                    serverGuildCounts[server]
                ) {

                    majorGuilds =
                        Object.entries(
                            serverGuildCounts[server]
                        )
                        .sort(
                            (a, b) =>
                                b[1] - a[1]
                        )
                        .slice(0, 5);

                }


                /*
                 * ギルド表示HTML
                 */

                let guildHtml = "";


                if (
                    majorGuilds.length > 0
                ) {

                    guildHtml =
                        majorGuilds
                            .map(
                                ([guild, guildCount]) =>
                                    `
                                    <span class="server-major-guild">
                                        ${escapeHtml(guild)}
                                        <span class="server-major-guild-count">
                                            ${guildCount}
                                        </span>
                                    </span>
                                    `
                            )
                            .join("");

                }


                /*
                 * -------------------------
                 * 行作成
                 * -------------------------
                 */

                const row =
                    document.createElement(
                        "div"
                    );


                row.className =
                    "server-row";


                row.innerHTML =
                    `
                    <div class="server-name">
                        ${escapeHtml(server)}
                    </div>

                    <div class="server-bar-container">

                        <div
                            class="server-bar"
                            style="width:${width}%"
                        ></div>

                    </div>

                    <div class="server-count">
                        ${count}人
                    </div>

                    <div class="server-major-guilds">
                        ${guildHtml}
                    </div>
                    `;


                container.appendChild(
                    row
                );

            }
        );


    /*
     * ========================================
     * Eda / Virba
     * ========================================
     */

    document.getElementById(
        "eda"
    ).textContent =
        Number(
            data.server.eda
        ).toLocaleString();


    document.getElementById(
        "virba"
    ).textContent =
        Number(
            data.server.virba
        ).toLocaleString();

}

/* ========================= */
/* ギルド */
/* ========================= */

function displayGuilds(data) {

    document.getElementById(
        "guild-members"
    ).textContent =
        Number(
            data.guild.members
        ).toLocaleString();


    document.getElementById(
        "no-guild"
    ).textContent =
        Number(
            data.guild.no_guild
        ).toLocaleString();


    const container =
        document.getElementById(
            "guild-list"
        );


    container.innerHTML = "";


    const guilds =
        data.guild.top20;


    /*
     * 1位の人数を基準にする
     */

    const maxCount =
        guilds.length > 0
            ? Math.max(
                ...guilds.map(
                    guild => guild.count
                )
            )
            : 0;


    guilds.forEach(
        guild => {

            const width =
                maxCount > 0
                    ? (
                        guild.count /
                        maxCount *
                        100
                    )
                    : 0;


            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "guild-row";


            row.innerHTML =
                `
                <div class="guild-rank">
                    ${guild.rank}
                </div>

                <div class="guild-name">
                    ${escapeHtml(
                        guild.guild
                    )}
                </div>

                <div class="guild-bar-container">

                    <div
                        class="guild-bar"
                        style="width:${width}%"
                    ></div>

                </div>

                <div class="guild-count">
                    ${guild.count}人
                </div>
                `;


            container.appendChild(
                row
            );

        }
    );

}



/* ========================= */
/* 日付フォーマット */
/* ========================= */

function formatDate(date) {

    if (!date) {

        return "-";

    }


    if (
        /^\d{8}$/.test(
            String(date)
        )
    ) {

        const value =
            String(date);


        return (
            value.substring(0, 4)
            + "/"
            + value.substring(4, 6)
            + "/"
            + value.substring(6, 8)
        );

    }


    return date;

}


/* ========================= */
/* HTMLエスケープ */
/* ========================= */

function escapeHtml(text) {

    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        text ?? "";


    return div.innerHTML;

}


/* ========================= */
/* 実行 */
/* ========================= */

loadData();