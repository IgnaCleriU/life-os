package lifeos.adapters.rest;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;
import tools.jackson.databind.json.JsonMapper;

/**
 * Guardia de la API REST, como {@code auth.py} en Python (ADR 0009, 0010).
 *
 * <ul>
 *   <li><b>Host:</b> solo {@code localhost}, {@code 127.0.0.1} y {@code ::1},
 *       más los nombres de {@code LIFEOS_ALLOWED_HOSTS} (por ejemplo los de
 *       Tailscale en un VPS). Bloquea el DNS rebinding: una página de
 *       {@code evil.example} que resuelve a 127.0.0.1 sigue mandando su Host.
 *   <li><b>Token:</b> toda ruta salvo {@code /health} y la web estática
 *       ({@code /}, {@code /app/**}, ver {@link WebPaths}) exige
 *       {@code Authorization: Bearer <token>}. El host se chequea primero.
 * </ul>
 *
 * <p>Con {@code LIFEOS_API_AUTH=disabled} la guardia entera se apaga (host
 * incluido), igual que en Python. Con la auth encendida y sin token falla
 * cerrado: todo responde 401.
 */
@Component
class LocalGuardFilter extends OncePerRequestFilter {

    private static final Set<String> LOOPBACK_HOSTS = Set.of("localhost", "127.0.0.1", "::1");
    private static final Set<String> OPEN_PATHS = Set.of("/health");

    private final JsonMapper json;
    private final boolean authEnabled;
    private final byte[] token;
    private final Set<String> allowedHosts;

    LocalGuardFilter(
            JsonMapper json,
            @Value("${lifeos.api.auth:enabled}") String auth,
            @Value("${lifeos.api.token:}") String token,
            @Value("${lifeos.api.allowed-hosts:}") String extraHosts) {
        this.json = json;
        this.authEnabled = parseAuth(auth);
        this.token = token == null || token.isBlank() ? null : token.getBytes(StandardCharsets.UTF_8);
        Set<String> hosts = new HashSet<>(LOOPBACK_HOSTS);
        hosts.addAll(normalizeHosts(extraHosts));
        this.allowedHosts = Set.copyOf(hosts);
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        return !authEnabled || OPEN_PATHS.contains(request.getRequestURI());
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        // Sin header Host (HTTP/1.0) no hay nombre al que confiar: como en Python,
        // se trata como vacío y se rechaza.
        String host = hostname(request.getHeader(HttpHeaders.HOST));
        if (host == null || !allowedHosts.contains(host)) {
            reject(response, HttpStatus.FORBIDDEN, "forbidden_host",
                    "The API only answers requests addressed to an allowed host.");
            return;
        }
        // La web estática (/, /app, /app/**) no lleva datos personales: se lee
        // (GET/HEAD) con el host validado pero sin token (WebPaths falla cerrado).
        // Cualquier otro método sigue exigiendo token.
        if (WebPaths.isWeb(request) && isReadMethod(request.getMethod())) {
            chain.doFilter(request, response);
            return;
        }
        if (token == null) {
            reject(response, HttpStatus.UNAUTHORIZED, "unauthorized",
                    "No API token is configured. Set LIFEOS_API_TOKEN (or LIFEOS_API_AUTH=disabled "
                            + "for local development only).");
            return;
        }
        if (!hasValidToken(request.getHeader(HttpHeaders.AUTHORIZATION))) {
            reject(response, HttpStatus.UNAUTHORIZED, "unauthorized", "Missing or invalid bearer token.");
            return;
        }
        chain.doFilter(request, response);
    }

    private static boolean isReadMethod(String method) {
        return "GET".equalsIgnoreCase(method) || "HEAD".equalsIgnoreCase(method);
    }

    private boolean hasValidToken(String authorization) {
        if (authorization == null) {
            return false;
        }
        int space = authorization.indexOf(' ');
        String scheme = space < 0 ? authorization : authorization.substring(0, space);
        String presented = space < 0 ? "" : authorization.substring(space + 1).strip();
        // Bytes UTF-8 y comparación en tiempo constante: un header con caracteres
        // raros da 401, no una excepción.
        return scheme.equalsIgnoreCase("bearer")
                && MessageDigest.isEqual(presented.getBytes(StandardCharsets.UTF_8), token);
    }

    private void reject(HttpServletResponse response, HttpStatus status, String code, String message)
            throws IOException {
        response.setStatus(status.value());
        if (status == HttpStatus.UNAUTHORIZED) {
            response.setHeader(HttpHeaders.WWW_AUTHENTICATE, "Bearer");
        }
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding(StandardCharsets.UTF_8);
        json.writeValue(response.getOutputStream(), Map.of("error", Map.of("code", code, "message", message)));
    }

    /**
     * Exactamente {@code enabled} o {@code disabled}, como el {@code Literal} de Python:
     * sin recortar ni pasar a minúsculas. Cualquier otro valor, incluido el vacío,
     * es un error de configuración. (El valor por defecto lo pone el placeholder
     * de {@code application.properties}.)
     */
    static boolean parseAuth(String value) {
        return switch (value == null ? "" : value) {
            case "enabled" -> true;
            case "disabled" -> false;
            default -> throw new IllegalArgumentException(
                    "LIFEOS_API_AUTH debe ser exactamente 'enabled' o 'disabled', no: '" + value + "'");
        };
    }

    /** {@code LIFEOS_ALLOWED_HOSTS} normalizado: minúsculas, sin punto final, sin vacíos. */
    static Set<String> normalizeHosts(String csv) {
        if (csv == null) {
            return Set.of();
        }
        return Arrays.stream(csv.split(","))
                .map(h -> h.strip().toLowerCase(Locale.ROOT))
                .map(h -> h.endsWith(".") ? h.substring(0, h.length() - 1) : h)
                .filter(h -> !h.isEmpty())
                .collect(Collectors.toUnmodifiableSet());
    }

    /** Nombre de host de un header {@code Host}, con o sin puerto; null si no se puede leer. */
    static String hostname(String hostHeader) {
        if (hostHeader == null || hostHeader.isEmpty()) {
            return null;
        }
        try {
            String host = URI.create("//" + hostHeader).getHost();
            if (host == null) {
                return null;
            }
            if (host.startsWith("[") && host.endsWith("]")) {
                host = host.substring(1, host.length() - 1);
            }
            // Sin quitar el punto final: urlsplit().hostname de Python lo conserva,
            // así que "localhost." es 403 en los dos backends.
            return host.toLowerCase(Locale.ROOT);
        } catch (IllegalArgumentException e) {
            return null;
        }
    }
}
