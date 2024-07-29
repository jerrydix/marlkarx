const { HLTV } = require('hltv')

async function getCurrentMajorID() {
    return HLTV.getEvents({eventType: "MAJOR"}).then(res => {
        return res[0].id;
    })
}

async function getPlayerByName(name) {
    return HLTV.getPlayerByName(name).then(res => {
        return res
    })
}

async function getMatches() {
    return HLTV.getMatches().then(res => {
        return res
    })
}

async function getMajorEvents() {
    return HLTV.getEvents({eventType: "MAJOR"}).then(res => {
        return res
    })
}

async function getAllMajorResults(currentMajorID) {
    if (currentMajorID === -1) {
        await getCurrentMajorID()
    }
    return HLTV.getResults({ eventIds: currentMajorID}).then(res => {
        return res
    })
}

async function getTodaysResults() {
    let currentDate = new Date().toJSON().slice(0, 10);
    return HLTV.getResults({startDate: currentDate, endDate: currentDate}).then(res => {
        return res
    })
}

async function getTodaysMajorResults(currentMajorID) {
    if (currentMajorID === -1) {
        await getCurrentMajorID()
    }
    let currentDate = new Date().toJSON().slice(0, 10);
    return HLTV.getResults({startDate: currentDate, endDate: currentDate, eventIds: currentMajorID}).then(res => {
        return res
    })
}

async function getAllMajorMatches(currentMajorID) {
    if (currentMajorID === -1) {
        await getCurrentMajorID()
    }
    return HLTV.getMatches({eventIds: currentMajorID}).then(res => {
        return res
    })
}

async function getLiveMajorMatchesInfo(currentMajorID) {
    let matches = await getAllMajorMatches(currentMajorID);
    let matchesInfo = [];
        for (let i = 0; i < matches.length; i++) {
            setTimeout(async () => {
                if (matches[i].live) {
                    let match = await getMajorMatch(matches[i].id);
                    matchesInfo.push(match)
                }
            }, 1000)
        }
    return matchesInfo
}

async function getMajorMatch(matchID) {
    return HLTV.getMatch({id: matchID}).then(res => {
        return res
    })
}

module.exports = {getCurrentMajorID, getPlayerByName, getMatches, getMajorEvents, getAllMajorResults, getTodaysMajorResults, getTodaysResults, getAllMajorMatches, getLiveMajorMatchesInfo, getMajorMatch}