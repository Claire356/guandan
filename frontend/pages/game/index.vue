<template>
  <view class="table-page safe-bottom" @touchstart="ensureBgm" @click="ensureBgm">
    <view class="table-head">
      <u-icon name="arrow-left" color="#fff" size="24" @click="back" />
      <text>第 {{ store.game?.round_number || 1 }} 局</text>
      <view class="head-tools">
        <view class="music-toggle" @click.stop="toggleBgm"><text>{{ musicEnabled ? '♫' : '♩' }}</text></view>
        <u-tag :text="store.offlineDemo ? '离线演示' : '在线训练'" size="mini" bgColor="rgba(255,255,255,.16)" borderColor="transparent" color="#fff" />
      </view>
    </view>
    <view class="level-banner"><text>当前级牌</text><strong>打{{ currentLevel }}</strong></view>

    <view class="game-table">
      <view v-for="seat in aiSeats" :key="seat.player.name" class="player" :class="[seat.position,{ 'has-power':powerHolder === seat.player.name }]">
        <image class="avatar-image" :src="seat.player.avatar" mode="aspectFill" />
        <text>{{ seat.player.name }}</text><text class="count">{{ seat.player.hand_count }}张</text>
      </view>
      <view v-for="name in playerNames" :key="name" class="table-play" :class="playPosition[name]">
        <view v-if="actionFor(name)?.cards?.length" class="play-cards">
          <PlayingCard v-for="(card,index) in actionFor(name).cards" :key="`${name}-${index}`" :card="card" disabled />
        </view>
        <text v-else-if="actionFor(name)?.is_pass" class="pass-mark">PASS</text>
      </view>
      <view class="desk-center">
        <text class="desk-label">本轮牌桌</text>
        <text v-if="!tableActions.length" class="empty-desk">等待首出</text>
        <text class="last-play">{{ lastPlayerText }}</text>
      </view>
      <view v-if="powerTransfer" class="power-transfer-animation">
        <view class="power-orb">♛</view><text>牌权交接</text><strong>{{ powerTransfer.player_name }}</strong>
      </view>
      <scroll-view v-if="tableActions.length" scroll-y class="played-history" :scroll-top="historyScrollTop">
        <view
          v-for="(action,index) in tableActions"
          :key="`action-${index}`"
          class="played-action"
          :class="{ latest: index === tableActions.length - 1 }"
        >
          <text class="action-player">{{ action.player }}</text>
          <view v-if="action.cards?.length" class="history-cards">
            <PlayingCard v-for="(card,cardIndex) in action.cards" :key="`${index}-${cardIndex}`" :card="card" disabled />
          </view>
          <text v-else class="history-pass">PASS</text>
        </view>
      </scroll-view>
      <view class="turn-pill">{{ turnText }}</view>
    </view>

    <view class="hand-panel">
      <view class="row-between"><text class="hand-title">我的手牌</text><text class="muted">已选 {{ store.selectedIndices.length }} 张</text></view>
      <scroll-view scroll-x class="hand-scroll">
        <view class="hand-row">
          <PlayingCard v-for="(card, index) in store.hand" :key="`${card}-${index}`" :card="card" :selected="store.selectedIndices.includes(index)" @select="store.toggleCard(index)" />
        </view>
      </scroll-view>
      <view class="actions">
        <u-button plain color="#d8b65b" text="AI推荐" @click="goRecommend" />
        <u-button plain color="#567064" text="PASS" :disabled="store.aiThinking" @click="pass" />
        <u-button type="primary" color="#0b5d3b" text="出牌" :loading="store.aiThinking" :disabled="store.aiThinking" @click="play" />
      </view>
      <u-button class="finish-link" type="primary" plain color="#0b5d3b" size="small" text="结束演示并查看结算" @click="finish" />
    </view>
  </view>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { onHide, onShow } from '@dcloudio/uni-app'
import { useGameStore } from '@/store/game'
import PlayingCard from '@/components/PlayingCard.vue'
const store = useGameStore()
const musicEnabled = ref(true)
let bgm = null
let musicStarted = false

// 牌桌背景音乐使用独立音频上下文，循环播放且不会阻塞出牌操作。
const startBgm = () => {
  if (!bgm || !musicEnabled.value) return
  const playResult = bgm.play()
  if (playResult?.catch) playResult.catch(() => { musicStarted = false })
}

// H5 浏览器可能禁止无交互自动播放，首次点击牌桌时再次尝试启动。
const ensureBgm = () => {
  if (!musicStarted && musicEnabled.value) startBgm()
}

const toggleBgm = () => {
  musicEnabled.value = !musicEnabled.value
  if (musicEnabled.value) startBgm()
  else {
    bgm?.pause()
    musicStarted = false
  }
}

onMounted(() => {
  // H5 优先使用浏览器原生 Audio；App/小程序继续使用 UniApp 音频上下文。
  // #ifdef H5
  // M4A 由用户提供的 OGG 无损流程转码，兼容 iPhone Safari 与桌面浏览器。
  bgm = new Audio('/audio/guandan-table-bgm.m4a')
  bgm.addEventListener('play', () => { musicStarted = true })
  bgm.addEventListener('error', () => { musicStarted = false })
  // #endif
  // #ifndef H5
  bgm = uni.createInnerAudioContext()
  bgm.src = '/audio/guandan-table-bgm.ogg'
  bgm.onPlay(() => { musicStarted = true })
  bgm.onError(() => { musicStarted = false })
  // #endif
  bgm.loop = true
  bgm.volume = 0.28
  bgm.autoplay = true
  startBgm()
})
onShow(() => { if (musicEnabled.value) startBgm() })
onHide(() => { bgm?.pause(); musicStarted = false })
onBeforeUnmount(() => {
  if (typeof bgm?.stop === 'function') bgm.stop()
  else bgm?.pause()
  if (typeof bgm?.destroy === 'function') bgm.destroy()
  else if (bgm) bgm.src = ''
  bgm = null
  musicStarted = false
})
const tableActions = computed(() => store.game?.state?.table_plays || [])
const currentLevel = computed(() => store.game?.currentLevel || store.game?.state?.current_level || '2')
const powerTransfer = computed(() => store.game?.state?.power_transfer || null)
const powerHolder = computed(() => store.game?.state?.power_holder_name || null)
const historyScrollTop = computed(() => tableActions.value.length * 120)
const playerNames = computed(() => (store.game?.players || []).map(player => player.name))
const aiSeats = computed(() => {
  const players = store.game?.players || []
  return [
    { player: players[2] || {name:'AI',avatar:'',hand_count:27}, position:'top' },
    { player: players[1] || {name:'AI',avatar:'',hand_count:27}, position:'left' },
    { player: players[3] || {name:'AI',avatar:'',hand_count:27}, position:'right' }
  ]
})
const playPosition = computed(() => {
  const names = playerNames.value
  return { [names[0]]:'bottom-play', [names[1]]:'left-play', [names[2]]:'top-play', [names[3]]:'right-play' }
})
const actionFor = name => [...tableActions.value].reverse().find(action => action.player === name)
const lastPlayerText = computed(() => store.game?.state?.last_action_text || (store.game?.state?.last_player_name ? `${store.game.state.last_player_name} · 最近出牌` : '本轮由你开始'))
const turnText = computed(() => {
  if (store.game?.winner) return '牌局已结束'
  const index = store.game?.state?.current_player_index || 0
  return index === 0 ? '轮到你出牌' : `轮到 ${store.game?.players?.[index]?.name || 'AI'}出牌`
})
const playerCount = name => store.game?.players?.find(player => player.name === name)?.hand_count ?? 27
const back = () => uni.navigateBack()
const toast = title => uni.showToast({ title, icon: 'none' })
const play = async () => { try { await store.playSelected(); toast('出牌成功') } catch (error) { toast(error.message) } }
const pass = async () => { try { await store.pass(); toast('已过牌') } catch (error) { toast(error.message) } }
const goRecommend = () => uni.navigateTo({ url: '/pages/recommend/index' })
const finish = () => { store.finishDemo(); uni.navigateTo({ url: '/pages/settlement/index' }) }
</script>

<style scoped lang="scss">
.table-page { min-height: 100vh; background: #075337; color: #fff; }
.table-head { height: 104rpx; padding: 38rpx 28rpx 16rpx; display: flex; align-items: center; justify-content: space-between; font-weight: 700; }
.head-tools { display:flex; align-items:center; gap:12rpx; }.music-toggle { width:48rpx; height:48rpx; display:flex; align-items:center; justify-content:center; border:1rpx solid rgba(255,255,255,.28); border-radius:50%; background:rgba(255,255,255,.14); }.music-toggle text { color:#f4d66f; font-size:29rpx; font-weight:800; }
.level-banner { width:210rpx; margin:0 auto 12rpx; padding:8rpx 18rpx; display:flex; justify-content:space-between; align-items:center; border:1rpx solid rgba(244,214,111,.55); border-radius:99rpx; background:rgba(0,0,0,.14); font-size:21rpx; }.level-banner strong { color:#f4d66f; font-size:27rpx; }
.game-table { position: relative; height: 670rpx; margin: 0 18rpx; overflow: hidden; border: 2rpx solid rgba(216,182,91,.42); border-radius: 42rpx; background: radial-gradient(circle, #168257 0, #0e6b47 60%, #09553a 100%); box-shadow: inset 0 0 70rpx rgba(0,0,0,.2); }
.player { position: absolute; display: flex; flex-direction: column; align-items: center; gap: 4rpx; font-size: 23rpx; }.player.top { top: 24rpx; left: 50%; transform: translateX(-50%); }.player.left { left: 20rpx; top: 250rpx; }.player.right { right: 20rpx; top: 250rpx; }
.player.has-power .avatar-image { border-color:#ffd86a; box-shadow:0 0 28rpx rgba(255,216,106,.9); animation:power-glow 1.5s ease-in-out infinite; }
.power-transfer-animation { position:absolute; z-index:8; left:50%; top:42%; transform:translate(-50%,-50%); display:flex; flex-direction:column; align-items:center; padding:18rpx 28rpx; border-radius:22rpx; color:#fff; background:rgba(2,48,31,.88); box-shadow:0 0 36rpx rgba(255,216,106,.6); animation:power-appear .45s ease-out; }.power-transfer-animation .power-orb { width:66rpx; height:66rpx; display:flex; align-items:center; justify-content:center; border-radius:50%; color:#684c00; background:radial-gradient(circle,#fff1a8,#ffb51f); box-shadow:0 0 28rpx #ffd86a; font-size:34rpx; }.power-transfer-animation text { margin-top:10rpx; color:#ffd86a; font-size:21rpx; }.power-transfer-animation strong { margin-top:4rpx; font-size:27rpx; }
@keyframes power-appear { from { opacity:0; transform:translate(-50%,-50%) scale(.55); } to { opacity:1; transform:translate(-50%,-50%) scale(1); } }
@keyframes power-glow { 50% { box-shadow:0 0 48rpx rgba(255,216,106,1); } }
.avatar-image { width:72rpx; height:72rpx; border:3rpx solid rgba(255,255,255,.78); border-radius:50%; background:#164d38; box-shadow:0 6rpx 18rpx rgba(0,0,0,.22); }.count { font-size: 20rpx; color: rgba(255,255,255,.65); }
.desk-center { position: absolute; left: 50%; top: 49%; transform: translate(-50%,-50%); text-align: center; }.desk-label,.last-play { display: block; font-size: 22rpx; color: rgba(255,255,255,.68); }.empty-desk { display:block; margin:18rpx 0; color:rgba(255,255,255,.55); font-size:25rpx; }
.table-play { position:absolute; z-index:2; min-width:90rpx; min-height:74rpx; display:flex; align-items:center; justify-content:center; }.top-play { top:120rpx; left:50%; transform:translateX(-50%); }.left-play { left:105rpx; top:285rpx; }.right-play { right:105rpx; top:285rpx; }.bottom-play { bottom:92rpx; left:50%; transform:translateX(-50%); }
.play-cards { display:flex; justify-content:center; }.play-cards :deep(.card) { width:54rpx; height:78rpx; flex-basis:54rpx; padding:6rpx; margin-left:-16rpx; border-radius:7rpx; }.play-cards :deep(.card:first-child) { margin-left:0; }.play-cards :deep(.card__label) { font-size:20rpx; }.play-cards :deep(.card__suit) { margin-top:4rpx; font-size:18rpx; }.pass-mark { padding:6rpx 12rpx; border-radius:10rpx; background:rgba(0,0,0,.2); color:rgba(255,255,255,.72); font-size:21rpx; font-weight:700; }
.played-history { position:absolute; z-index:3; left:50%; top:50%; width:330rpx; height:250rpx; transform:translate(-50%,-50%); padding:8rpx; border-radius:16rpx; background:rgba(4,54,35,.34); box-sizing:border-box; }.played-action { display:flex; align-items:center; min-height:50rpx; margin:5rpx 0; padding:5rpx 8rpx; border:2rpx solid transparent; border-radius:10rpx; opacity:.72; }.played-action.latest { border-color:#f4d66f; background:rgba(244,214,111,.15); box-shadow:0 0 16rpx rgba(244,214,111,.55); opacity:1; }.action-player { width:58rpx; flex:0 0 58rpx; color:#fff; font-size:18rpx; font-weight:700; }.history-cards { display:flex; min-width:0; }.history-cards :deep(.card) { width:42rpx; height:58rpx; flex-basis:42rpx; padding:4rpx; margin-left:-12rpx; border-radius:5rpx; }.history-cards :deep(.card:first-child) { margin-left:0; }.history-cards :deep(.card__label) { font-size:16rpx; }.history-cards :deep(.card__suit) { margin-top:2rpx; font-size:14rpx; }.played-action.latest .history-cards :deep(.card) { border-color:#f4d66f; box-shadow:0 0 10rpx rgba(244,214,111,.8); transform:translateY(-3rpx); }.history-pass { color:rgba(255,255,255,.7); font-size:18rpx; font-weight:700; }
.turn-pill { position: absolute; bottom: 28rpx; left: 50%; transform: translateX(-50%); padding: 10rpx 26rpx; border-radius: 99rpx; color: #3d3216; background: #e4c66d; font-size: 24rpx; font-weight: 700; }
.hand-panel { margin-top: -12rpx; padding: 28rpx 24rpx 22rpx; border-radius: 30rpx 30rpx 0 0; background: #f3f7f4; color: #18372a; }.hand-title { font-weight: 800; }
.hand-scroll { width: 100%; height: 164rpx; margin-top: 24rpx; }.hand-row { min-width: max-content; display: flex; gap: 7rpx; padding: 22rpx 4rpx; }
.actions { display: grid; grid-template-columns: 1fr 1fr 1.4fr; gap: 14rpx; }.finish-link { margin-top: 18rpx; }
@media screen and (min-width: 768px) {
  .table-page { max-width: 980px; margin: 0 auto; box-shadow: 0 0 50px rgba(5, 65, 42, .18); }
  .game-table { height: 610px; }
  .hand-panel { padding-left: 36px; padding-right: 36px; }
}
</style>
