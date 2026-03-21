package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/valyala/fasthttp"

	"xiuxian-gateway/internal/cache"
	"xiuxian-gateway/internal/handler"
	"xiuxian-gateway/internal/proxy"
)

func main() {
	var (
		listen      = flag.String("listen", ":8080", "gateway listen address")
		redisAddr   = flag.String("redis", "127.0.0.1:6379", "redis address")
		redisPwd    = flag.String("redis-pwd", "", "redis password")
		redisDB     = flag.Int("redis-db", 0, "redis db number")
		backendURL  = flag.String("backend", "http://127.0.0.1:11450", "python backend URL")
		internalTok = flag.String("token", "", "X-Internal-Token for backend auth")
		staticDir   = flag.String("static", "", "path to xiuxian-web/dist for serving static files")
	)
	flag.Parse()

	// ── Redis ──
	store := cache.New(*redisAddr, *redisPwd, *redisDB)
	if err := store.Ping(nil); err != nil {
		log.Printf("WARNING: Redis not available (%v), running without cache", err)
	} else {
		log.Printf("Redis connected: %s db=%d", *redisAddr, *redisDB)
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

	// ── fasthttp server ──
	var h fasthttp.RequestHandler = router.Handle

	// Brotli/gzip compression
	h = fasthttp.CompressHandlerBrotliLevel(h, fasthttp.CompressBrotliDefaultCompression, fasthttp.CompressDefaultCompression)

	// Static file serving (if configured)
	if *staticDir != "" {
		fs := &fasthttp.FS{
			Root:               *staticDir,
			IndexNames:         []string{"index.html"},
			GenerateIndexPages: false,
			Compress:           true,
			CompressBrotli:     true,
			CacheDuration:      365 * 24 * 60 * 60, // 1 year for hashed assets
		}
		fsHandler := fs.NewRequestHandler()

		apiHandler := h
		h = func(ctx *fasthttp.RequestCtx) {
			path := string(ctx.Path())
			// API requests → Go gateway
			if len(path) >= 4 && path[:4] == "/api" {
				apiHandler(ctx)
				return
			}
			// Static files → serve from dist/
			fsHandler(ctx)
			// SPA fallback: if 404 and not a file, serve index.html
			if ctx.Response.StatusCode() == 404 {
				ctx.Request.SetRequestURI("/index.html")
				fsHandler(ctx)
			}
		}
	}

	server := &fasthttp.Server{
		Handler:            h,
		Name:               "xiuxian-gateway",
		MaxRequestBodySize: 1 << 20, // 1MB
		ReadTimeout:        10_000_000_000,
		WriteTimeout:       10_000_000_000,
		MaxConnsPerIP:      100,
	}

	// ── Graceful shutdown ──
	go func() {
		sig := make(chan os.Signal, 1)
		signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
		<-sig
		log.Println("Shutting down...")
		_ = server.Shutdown()
	}()

	fmt.Printf("xiuxian-gateway listening on %s\n", *listen)
	fmt.Printf("  backend: %s\n", *backendURL)
	fmt.Printf("  redis:   %s/%d\n", *redisAddr, *redisDB)
	if *staticDir != "" {
		fmt.Printf("  static:  %s\n", *staticDir)
	}

	if err := server.ListenAndServe(*listen); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
