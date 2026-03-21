package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"github.com/valyala/fasthttp"

	"xiuxian-gateway/internal/cache"
	"xiuxian-gateway/internal/handler"
	"xiuxian-gateway/internal/proxy"
)

func main() {
	var (
		listen      = flag.String("listen", ":8080", "listen address")
		redisAddr   = flag.String("redis", "127.0.0.1:6379", "redis address")
		redisPwd    = flag.String("redis-pwd", "", "redis password")
		redisDB     = flag.Int("redis-db", 0, "redis db")
		backendURL  = flag.String("backend", "http://127.0.0.1:11450", "python backend")
		internalTok = flag.String("token", "", "X-Internal-Token")
	)
	flag.Parse()

	// ── Auto-detect static dir ──
	// Look for index.html in same directory as the binary
	exe, _ := os.Executable()
	exeDir := filepath.Dir(exe)
	staticDir := ""
	for _, candidate := range []string{
		filepath.Join(exeDir, "index.html"),             // same dir (deployed)
		filepath.Join(exeDir, "..", "dist", "index.html"), // dev: gateway/../dist
	} {
		if _, err := os.Stat(candidate); err == nil {
			staticDir = filepath.Dir(candidate)
			break
		}
	}

	// ── Redis ──
	store := cache.New(*redisAddr, *redisPwd, *redisDB)
	if err := store.Ping(nil); err != nil {
		log.Printf("⚠ Redis unavailable (%v), pass-through mode", err)
	} else {
		log.Printf("✓ Redis %s/%d", *redisAddr, *redisDB)
	}
	defer store.Close()

	// ── Backend ──
	backend := proxy.NewBackend(*backendURL)

	// ── Router ──
	router := &handler.Router{
		Store:   store,
		Backend: backend,
		Token:   *internalTok,
	}

	// ── Build handler chain ──
	var h fasthttp.RequestHandler = router.Handle

	// Brotli + gzip compression for API responses
	h = fasthttp.CompressHandlerBrotliLevel(h, fasthttp.CompressBrotliDefaultCompression, fasthttp.CompressDefaultCompression)

	// Static files (auto-detected)
	if staticDir != "" {
		fs := &fasthttp.FS{
			Root:               staticDir,
			IndexNames:         []string{"index.html"},
			GenerateIndexPages: false,
			Compress:           true,
			CompressBrotli:     true,
			CacheDuration:      365 * 24 * time.Hour,
		}
		fsHandler := fs.NewRequestHandler()
		apiHandler := h

		h = func(ctx *fasthttp.RequestCtx) {
			path := string(ctx.Path())
			if len(path) >= 4 && path[:4] == "/api" {
				apiHandler(ctx)
				return
			}
			fsHandler(ctx)
			if ctx.Response.StatusCode() == 404 {
				ctx.Response.Reset()
				ctx.Request.SetRequestURI("/index.html")
				fsHandler(ctx)
			}
		}
		log.Printf("✓ Static files: %s", staticDir)
	} else {
		log.Printf("⚠ No static dir found (API-only mode)")
	}

	server := &fasthttp.Server{
		Handler:            h,
		Name:               "xiuxian-gw",
		MaxRequestBodySize: 1 << 20,
		ReadTimeout:        10 * time.Second,
		WriteTimeout:       10 * time.Second,
		MaxConnsPerIP:      100,
	}

	go func() {
		sig := make(chan os.Signal, 1)
		signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
		<-sig
		log.Println("shutting down...")
		_ = server.Shutdown()
	}()

	fmt.Println("══════════════════════════════")
	fmt.Println("  修仙之路 · Gateway")
	fmt.Printf("  http://0.0.0.0%s\n", *listen)
	fmt.Printf("  backend → %s\n", *backendURL)
	fmt.Println("══════════════════════════════")

	if err := server.ListenAndServe(*listen); err != nil {
		log.Fatalf("server: %v", err)
	}
}
