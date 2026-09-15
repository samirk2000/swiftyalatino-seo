<?php
/**
 * SWIFTYALATINO - Snippets opcionales para functions.php (child theme)
 * Solo aplican si el sitio corre en WordPress según lo definido en .cursorrules.
 * No pegar en el theme principal: usar un child theme o el plugin "Code Snippets".
 */

// 1) Inyecta el FAQ Schema en el <head> del home si no se usa Rank Math Schema Generator
add_action('wp_head', function () {
    if (! is_front_page()) {
        return;
    }
    $faq_json = file_get_contents(get_stylesheet_directory() . '/seo/faq-schema.json');
    if ($faq_json) {
        echo '<script type="application/ld+json">' . $faq_json . '</script>' . "\n";
    }
});

// 2) Desactiva emojis y embeds innecesarios de WP para mejorar Core Web Vitals
add_action('init', function () {
    remove_action('wp_head', 'print_emoji_detection_script', 7);
    remove_action('wp_print_styles', 'print_emoji_styles');
    remove_action('wp_head', 'wp_oembed_add_discovery_links');
});

// 3) Precarga de la fuente principal para reducir CLS/LCP
add_action('wp_head', function () {
    echo '<link rel="preload" as="style" href="' . esc_url(get_stylesheet_directory_uri() . '/assets/css/style.css') . '">' . "\n";
}, 1);
