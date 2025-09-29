/**
 * 全局Loading Modal组件
 * 对应Django模板中的globalLoadingModal
 * 支持多种加载场景：简历生成、求职信生成、匹配等
 */
import React from 'react';
import PropTypes from 'prop-types';

const LoadingModal = ({ show, title, subtitle, type = 'default' }) => {
  if (!show) return null;

  // 根据类型显示不同的标题和图标
  const getConfig = () => {
    switch (type) {
      case 'resume':
        return {
          title: title || 'Generating your custom resume, please wait...',
          subtitle: subtitle || 'Optimizing your CV for the target position...',
        };
      case 'cover-letter':
        return {
          title: title || 'Generating your cover letter, please wait...',
          subtitle: subtitle || 'Crafting a compelling introduction for your application...',
        };
      case 'matching':
        return {
          title: title || 'Matching in progress, please wait...',
          subtitle: subtitle || 'Finding the best job opportunities for you...',
        };
      default:
        return {
          title: title || 'Processing, please wait...',
          subtitle: subtitle || '',
        };
    }
  };

  const config = getConfig();

  return (
    <div
      className="modal fade show"
      style={{
        display: 'block',
        backgroundColor: 'rgba(0,0,0,0.5)',
        backdropFilter: 'blur(4px)'
      }}
      tabIndex="-1"
      aria-hidden="true"
      data-bs-backdrop="static"
      data-bs-keyboard="false"
    >
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content text-center p-4">
          <div className="modal-body">
            <div
              className="spinner-border text-primary mb-3"
              role="status"
              style={{ width: '3rem', height: '3rem' }}
            >
              <span className="visually-hidden">Loading...</span>
            </div>
            <h5 className="modal-title" id="globalLoadingModalLabel">
              {config.title}
            </h5>
            {config.subtitle && (
              <div id="globalLoadingModalSubtext" className="mt-2 text-muted small">
                {config.subtitle}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

LoadingModal.propTypes = {
  show: PropTypes.bool.isRequired,
  title: PropTypes.string,
  subtitle: PropTypes.string,
  type: PropTypes.oneOf(['default', 'resume', 'cover-letter', 'matching']),
};

LoadingModal.defaultProps = {
  title: '',
  subtitle: '',
  type: 'default',
};

export default LoadingModal;
