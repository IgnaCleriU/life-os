package lifeos.adapters.rest;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.regex.Pattern;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.server.WebServerFactoryCustomizer;
import org.springframework.boot.web.server.servlet.ConfigurableServletWebServerFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Dirección de escucha del servidor. Loopback por defecto: aunque haya token,
 * en {@code 0.0.0.0} cualquier equipo de la LAN llegaría al puerto. Solo el
 * contenedor lo cambia, con {@code LIFEOS_BIND_ADDRESS}.
 *
 * <p>Se resuelve en código y no con {@code server.address=${...:127.0.0.1}}
 * porque un {@code LIFEOS_BIND_ADDRESS=} vacío (típico en un {@code .env})
 * llegaría como cadena vacía y Tomcat escucharía en todas las interfaces.
 */
@Configuration(proxyBeanMethods = false)
class BindAddressConfiguration {

    private static final Logger LOG = LoggerFactory.getLogger(BindAddressConfiguration.class);

    static final String LOOPBACK = "127.0.0.1";
    private static final Pattern IP_LITERAL = Pattern.compile("[0-9A-Fa-f:.]+");

    @Bean
    WebServerFactoryCustomizer<ConfigurableServletWebServerFactory> bindAddressCustomizer(
            @Value("${lifeos.bind-address:}") String configured) {
        InetAddress address = resolve(configured);
        // En Docker, un `LIFEOS_BIND_ADDRESS=` vacío en el .env pisa el 0.0.0.0 de la
        // imagen y el puerto publicado deja de responder: este log lo hace visible.
        LOG.info("Listening on {} (LIFEOS_BIND_ADDRESS='{}')", address.getHostAddress(),
                configured == null ? "" : configured);
        return factory -> factory.setAddress(address);
    }

    /** Vacío o en blanco = loopback; si no, el valor recortado. Inválido = el arranque falla. */
    static InetAddress resolve(String configured) {
        String value = configured == null ? "" : configured.strip();
        if (value.isEmpty()) {
            value = LOOPBACK;
        }
        // Solo literales IP: getByName con un nombre haría una consulta DNS.
        if (!IP_LITERAL.matcher(value).matches()) {
            throw invalid(configured, null);
        }
        try {
            return InetAddress.getByName(value);
        } catch (UnknownHostException e) {
            throw invalid(configured, e);
        }
    }

    private static IllegalStateException invalid(String configured, Exception cause) {
        return new IllegalStateException(
                "LIFEOS_BIND_ADDRESS no es una dirección IP válida: '" + configured + "'", cause);
    }
}
