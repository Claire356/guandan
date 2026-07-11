<script>
export default {
  onLaunch() {
    console.info('AI 掼蛋训练已启动')
    // #ifdef H5
    requestAnimationFrame(() => {
      document.getElementById('app-loading')?.classList.add('app-loading--hidden')
      window.setTimeout(() => document.getElementById('app-loading')?.remove(), 260)
    })
    // #endif
  },
  onPageNotFound() {
    uni.reLaunch({ url: '/pages/not-found/index' })
  }
}
</script>

<style lang="scss">
@import "uview-plus/index.scss";
@import "./styles/theme.scss";
</style>
