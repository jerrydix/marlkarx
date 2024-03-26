const { HLTV } = require('hltv')

HLTV.getPlayerByName({ name: "chrisJ" }).then(res => {
    console.log(res)
})