<template>
  <view class="report-page safe-bottom">
    <view class="report-shell">
      <view class="profile-card">
        <view class="profile-glow" />
        <view class="avatar-wrap">
          <image v-if="report.player?.avatar" class="profile-avatar" :src="report.player.avatar" mode="aspectFill" />
          <text v-else class="avatar-letter">{{ (report.player?.name || '你').slice(0, 1) }}</text>
        </view>
        <view class="profile-copy">
          <text class="eyebrow">PERSONALITY REPORT</text>
          <text class="nickname">{{ report.player?.name || '你' }}</text>
          <text class="profile-sub">本局行为画像</text>
        </view>
        <view class="overall"><text>{{ report.overall_score }}</text><small>综合评分</small></view>
      </view>

      <view class="title-card">
        <view class="title-main"><text class="title-emoji">{{ titleData.emoji }}</text><view><text class="title-kicker">你的掼蛋人格称号</text><text class="personality-title">{{ titleData.title }}</text></view></view>
        <text class="title-psychology">{{ titleData.psychology }}</text>
        <view class="quote"><text>{{ titleData.catchphrase }}</text></view>
        <view class="fun-tags"><text v-for="tag in titleData.tags" :key="tag"># {{ tag }}</text></view>
        <view class="title-detail"><text class="detail-label">打法画像</text><text>{{ titleData.playstyle }}</text></view>
        <view class="warning"><text>💡 {{ titleData.warning }}</text></view>
      </view>

      <view class="data-card">
        <view class="card-heading"><text>五维行为画像</text><text class="baseline">50 为人格分界线</text></view>
        <view class="score-table">
          <view class="score-row table-head"><text>维度</text><text>得分</text><text>人格结果</text></view>
          <view v-for="item in dimensions" :key="item.key" class="score-row">
            <view><text class="dimension-name">{{ dimensionLabels[item.key] }}</text><text class="explanation">{{ item.explanation }}</text></view>
            <text class="score-value">{{ Math.round(item.score) }}</text>
            <text class="result-chip">{{ item.tag }}</text>
          </view>
        </view>
      </view>

      <view class="tags-card">
        <text class="card-title">本局人格</text>
        <scroll-view scroll-x class="tags-scroll"><view class="tags"><text v-for="tag in report.tags" :key="tag">{{ tag }}</text></view></scroll-view>
      </view>

      <view class="ai-comment">
        <view class="ai-mark">AI</view>
        <view><text class="card-title">AI 综合点评</text><text class="comment-text">{{ report.summary }}</text></view>
      </view>

      <view class="actions"><u-button type="primary" color="#635bff" shape="circle" text="查看历史记录" @click="history" /><u-button plain color="#635bff" shape="circle" text="返回首页" @click="home" /></view>
    </view>
  </view>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useGameStore } from '@/store/game'

const store = useGameStore()
const fallback = {
  player:{name:'你',avatar:''}, overall_score:50,
  tags:['侵略型','合作型','冷静型','稳健型','果断型'],
  dimensions:[], summary:'行为样本仍较少，完成更多牌局后画像会更加准确。'
}
const report = computed(() => store.report || fallback)
const defaultTitle = { title:'未定义的神秘人', emoji:'❓', psychology:'完成更多对局后解锁专属称号。', playstyle:'当前行为样本不足。', catchphrase:'"再来一局看看。"', tags:['等待解锁'], warning:'多完成几局训练，画像会更加准确。' }
const titleData = computed(() => report.value.personality_title || defaultTitle)
const dimensions = computed(() => report.value.dimensions || [])
const dimensionLabels = { aggression:'侵略性', cooperation:'合作性', emotion:'情绪倾向', risk:'风险偏好', decision:'决策速度' }
onMounted(() => store.loadPersonalityReport())
const history = () => uni.navigateTo({ url:'/pages/history/index' })
const home = () => uni.reLaunch({ url:'/pages/index/index' })
</script>

<style scoped lang="scss">
.report-page { min-height:100vh; padding:28rpx; color:#161829; background:radial-gradient(circle at 90% 2%,rgba(99,91,255,.16),transparent 30%),linear-gradient(180deg,#f7f8fc,#edf0f8); }
.report-shell { width:100%; max-width:980px; margin:0 auto; }
.profile-card { position:relative; overflow:hidden; display:grid; grid-template-columns:auto 1fr auto; gap:24rpx; align-items:center; padding:34rpx; border:1rpx solid rgba(255,255,255,.9); border-radius:30rpx; color:#fff; background:linear-gradient(135deg,#191b35,#34345f 62%,#5b52db); box-shadow:0 24rpx 60rpx rgba(38,38,85,.22); }
.profile-glow { position:absolute; right:-80rpx; top:-120rpx; width:300rpx; height:300rpx; border-radius:50%; background:rgba(147,137,255,.32); filter:blur(20rpx); }
.avatar-wrap { z-index:1; width:112rpx; height:112rpx; overflow:hidden; display:flex; align-items:center; justify-content:center; border:4rpx solid rgba(255,255,255,.78); border-radius:30rpx; background:linear-gradient(135deg,#7770ff,#a98cff); box-shadow:0 12rpx 32rpx rgba(0,0,0,.24); }.profile-avatar { width:100%; height:100%; }.avatar-letter { font-size:44rpx; font-weight:900; }
.profile-copy { z-index:1; display:flex; flex-direction:column; }.eyebrow { color:#aaa7ff; font-size:19rpx; letter-spacing:2rpx; font-weight:700; }.nickname { margin:8rpx 0 4rpx; font-size:38rpx; font-weight:900; }.profile-sub { color:rgba(255,255,255,.62); font-size:23rpx; }
.overall { z-index:1; min-width:120rpx; text-align:center; }.overall text { display:block; font-size:58rpx; line-height:1; font-weight:900; color:#c9c5ff; }.overall small { display:block; margin-top:9rpx; color:rgba(255,255,255,.62); font-size:20rpx; }
.data-card,.tags-card,.ai-comment { margin-top:22rpx; padding:30rpx; border:1rpx solid rgba(98,91,170,.1); border-radius:26rpx; background:rgba(255,255,255,.92); box-shadow:0 14rpx 44rpx rgba(45,48,78,.08); }
.title-card { position:relative; overflow:hidden; margin-top:22rpx; padding:34rpx; border:1rpx solid rgba(120,104,255,.18); border-radius:28rpx; background:linear-gradient(145deg,#ffffff,#f3f0ff); box-shadow:0 18rpx 50rpx rgba(78,65,165,.12); }.title-main { display:flex; align-items:center; gap:20rpx; }.title-emoji { font-size:54rpx; }.title-kicker { display:block; color:#7a73a7; font-size:20rpx; letter-spacing:1rpx; }.personality-title { display:block; margin-top:5rpx; color:#332d83; font-size:38rpx; font-weight:950; }.title-psychology { display:block; margin-top:22rpx; color:#55566b; font-size:24rpx; line-height:1.75; }.quote { margin-top:20rpx; padding:20rpx; border-left:6rpx solid #756cff; border-radius:0 16rpx 16rpx 0; color:#403b83; background:rgba(117,108,255,.08); font-size:24rpx; line-height:1.65; font-weight:700; }.fun-tags { display:flex; flex-wrap:wrap; gap:10rpx; margin-top:18rpx; }.fun-tags text { padding:8rpx 13rpx; border-radius:99rpx; color:#625acb; background:#eae7ff; font-size:20rpx; }.title-detail { display:flex; flex-direction:column; gap:8rpx; margin-top:22rpx; color:#686a7e; font-size:22rpx; line-height:1.7; }.detail-label { color:#242641; font-weight:850; }.warning { margin-top:20rpx; padding:17rpx; border-radius:14rpx; color:#8b6420; background:#fff7df; font-size:21rpx; line-height:1.6; }
.card-heading { display:flex; justify-content:space-between; align-items:center; margin-bottom:18rpx; font-size:30rpx; font-weight:800; }.baseline { padding:7rpx 12rpx; border-radius:99rpx; color:#635bff; background:#efeeff; font-size:19rpx; font-weight:600; }
.score-table { overflow:hidden; border:1rpx solid #e9eaf2; border-radius:18rpx; }.score-row { display:grid; grid-template-columns:1fr 100rpx 130rpx; gap:12rpx; align-items:center; min-height:98rpx; padding:16rpx 20rpx; border-bottom:1rpx solid #ececf3; }.score-row:last-child { border:0; }.score-row.table-head { min-height:54rpx; color:#85889b; background:#f7f7fb; font-size:21rpx; }.dimension-name { display:block; font-size:25rpx; font-weight:750; }.explanation { display:block; margin-top:5rpx; color:#8b8d9d; font-size:19rpx; line-height:1.45; }.score-value { font-size:34rpx; font-weight:900; color:#3d3a8c; }.result-chip { justify-self:start; padding:7rpx 13rpx; border-radius:99rpx; color:#554dd2; background:#efeeff; font-size:21rpx; font-weight:750; }
.card-title { display:block; font-size:28rpx; font-weight:850; }.tags-scroll { margin-top:20rpx; white-space:nowrap; }.tags { display:flex; gap:12rpx; width:max-content; }.tags text { padding:13rpx 20rpx; border:1rpx solid #dcd9ff; border-radius:14rpx; color:#4f48c7; background:linear-gradient(135deg,#f4f3ff,#eceaff); font-size:23rpx; font-weight:750; }
.ai-comment { display:flex; gap:20rpx; align-items:flex-start; background:linear-gradient(135deg,#fff,#f5f4ff); }.ai-mark { flex:0 0 66rpx; height:66rpx; display:flex; align-items:center; justify-content:center; border-radius:18rpx; color:#fff; background:linear-gradient(135deg,#635bff,#9b72ff); font-weight:900; box-shadow:0 9rpx 22rpx rgba(99,91,255,.28); }.comment-text { display:block; margin-top:10rpx; color:#686b7c; font-size:24rpx; line-height:1.7; }
.actions { display:grid; grid-template-columns:1fr 1fr; gap:16rpx; margin-top:26rpx; }
@media screen and (max-width:500px) { .profile-card { grid-template-columns:auto 1fr; }.overall { grid-column:1/-1; display:flex; align-items:baseline; justify-content:center; gap:12rpx; }.score-row { grid-template-columns:1fr 60rpx 100rpx; padding:14rpx 12rpx; }.explanation { font-size:17rpx; } }
</style>
